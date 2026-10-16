#!/usr/bin/env bash
# One-time bench setup inside the bench container:
#   docker compose -p talentai-frappe exec bench bash /home/frappe/setup.sh
set -euo pipefail
FRAPPE_REF=${FRAPPE_REF:-v16.31.0}
ERPNEXT_REF=${ERPNEXT_REF:-v16.32.0}
HRMS_REF=${HRMS_REF:-640af1592a01}
cd /home/frappe/work
if [ ! -d frappe-bench ]; then
  bench init --frappe-branch "$FRAPPE_REF" --python python3.14 --skip-redis-config-generation --no-backups frappe-bench
fi
cd frappe-bench
bench set-config -g db_host mariadb
bench set-config -g redis_cache redis://redis-cache:6379
bench set-config -g redis_queue redis://redis-queue:6379
bench set-config -g redis_socketio redis://redis-queue:6379
bench set-config -gp webserver_port 18050
bench set-config -gp socketio_port 18051
bench set-config -gp developer_mode 1
[ -d apps/erpnext ] || bench get-app --branch "$ERPNEXT_REF" erpnext https://github.com/frappe/erpnext
if [ ! -d apps/hrms ]; then
  git clone --filter=blob:none https://github.com/frappe/hrms apps/hrms
  (cd apps/hrms && git checkout -q "$HRMS_REF")
  ./env/bin/pip install -q -e apps/hrms
  (cd apps/hrms && [ -f package.json ] && yarn install --frozen-lockfile --silent || true)
  bench build --app hrms
  grep -qx hrms sites/apps.txt || { [ -n "$(tail -c1 sites/apps.txt)" ] && echo >> sites/apps.txt; echo hrms >> sites/apps.txt; }
fi
# Our app: mounted read-only from the host, linked into the bench and installed editable.
if [ ! -e apps/ido_talent_ai ]; then
  ln -sfn /home/frappe/apps-src/ido_talent_ai apps/ido_talent_ai
  ./env/bin/pip install -q -e apps/ido_talent_ai
  grep -qx ido_talent_ai sites/apps.txt || { [ -n "$(tail -c1 sites/apps.txt)" ] && echo >> sites/apps.txt; echo ido_talent_ai >> sites/apps.txt; }
fi
# Procfile: web on the agreed port, no asset watcher, extra workers for the long queue (CV upload + OCR)
cat > Procfile <<'PROCFILE'
web: bench serve --port 18050
socketio: bench socketio
schedule: bench schedule
worker: bench worker 1>> logs/worker.log 2>> logs/worker.error.log
worker_long_1: bench worker --queue long 1>> logs/worker.log 2>> logs/worker.error.log
worker_long_2: bench worker --queue long 1>> logs/worker.log 2>> logs/worker.error.log
PROCFILE
echo "bench ready: $(ls apps | tr '\n' ' ')"
