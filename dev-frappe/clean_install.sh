#!/bin/bash
# Rehearse a clean install in a separate bench (inside the bench container):
# clone frappe/erpnext/hrms from the dev bench, `bench get-app` our app from its git repository,
# new site with ERPNext + HRMS, install-app, migrate, app tests, uninstall-app, platform check.
set -uo pipefail
W=/home/frappe/work
B=$W/clean-bench
SITE=clean.localhost
log() { echo "[clean] $*"; }
if [ ! -f "$B/.talentai-clean" ]; then
  log "new bench: local git clones of frappe/erpnext/hrms (same commits as the dev bench) + new virtualenv"
  rm -rf "$B"; mkdir -p "$B/apps" "$B/sites" "$B/config/pids" "$B/logs"
  for a in frappe erpnext hrms; do git clone -q "$W/frappe-bench/apps/$a" "$B/apps/$a"; (cd "$B/apps/$a" && git checkout -q "$(cd $W/frappe-bench/apps/$a && git rev-parse HEAD)"); done
  cd "$B" && uv venv -q env --seed --python python3.14 && uv pip install -q --python env/bin/python -e apps/frappe -e apps/erpnext -e apps/hrms || exit 1
  printf "frappe\nerpnext\nhrms\n" > sites/apps.txt
  echo "{}" > sites/common_site_config.json; touch .talentai-clean
  mkdir -p sites/assets   # no asset build here: the rehearsal is about install/migrate/tests/uninstall
fi
cd $B
if [ -e apps/ido_talent_ai ]; then rm -rf apps/ido_talent_ai; uv pip uninstall -q --python env/bin/python ido_talent_ai >/dev/null 2>&1; sed -i '/^ido_talent_ai$/d' sites/apps.txt; fi
bench set-config -g db_host mariadb >/dev/null; bench set-config -g redis_cache redis://redis-cache:6379 >/dev/null
bench set-config -g redis_queue redis://redis-queue:6379 >/dev/null; bench set-config -g redis_socketio redis://redis-queue:6379 >/dev/null
for d in /home/frappe/apps-src/ido_talent_ai /home/frappe/apps-src/ido_talent_ai/.git; do git config --global --get-all safe.directory | grep -qx $d || git config --global --add safe.directory $d; done
log "bench get-app from the app's git repository (branch $1)"
bench get-app --skip-assets --branch "$1" /home/frappe/apps-src/ido_talent_ai 2>&1 | tail -2
log "apps: $(ls apps | tr '\n' ' ')"
log "new site with ERPNext + HRMS"
bench new-site $SITE --force --db-root-password "$DB_ROOT_PASSWORD" --admin-password "$(python3 -c 'import secrets;print(secrets.token_urlsafe(16))')" --mariadb-user-host-login-scope='%' \
  --install-app erpnext --install-app hrms > $W/clean-site.log 2>&1 || { tail -20 $W/clean-site.log; exit 1; }
log "install-app ido_talent_ai"
bench --site $SITE install-app ido_talent_ai 2>&1 | tail -1
log "migrate"
bench --site $SITE migrate 2>&1 | tail -1
bench --site $SITE set-config allow_tests true >/dev/null
bench --site $SITE execute ido_talent_ai.scripts.seed_demo.company_only >/dev/null 2>&1 || bench --site $SITE set-config developer_mode 1
bench --site $SITE set-config developer_mode 1 >/dev/null
bench --site $SITE execute ido_talent_ai.scripts.seed_demo.company_only 2>&1 | tail -1
log "custom fields: $(bench --site $SITE mariadb -N -e "select count(*) from \`tabCustom Field\` where module='Talent AI'" 2>/dev/null)"
log "app tests"
bench --site $SITE run-tests --app ido_talent_ai --skip-before-tests 2>&1 | grep -E "^Ran|^OK|^FAILED"
log "uninstall-app"
bench --site $SITE uninstall-app ido_talent_ai --yes --no-backup 2>&1 | tail -2
log "after uninstall: custom fields $(bench --site $SITE mariadb -N -e "select count(*) from \`tabCustom Field\` where dt in ('Job Applicant','Job Opening') and fieldname like 'ai\_%'" 2>/dev/null), level-1 perms $(bench --site $SITE mariadb -N -e "select count(*) from \`tabCustom DocPerm\` where parent='Job Applicant' and permlevel=1" 2>/dev/null), AI doctypes $(bench --site $SITE mariadb -N -e "select count(*) from tabDocType where module='Talent AI'" 2>/dev/null)"
log "platform check: a Job Applicant can still be created"
bench --site $SITE execute frappe.client.insert --kwargs '{"doc": {"doctype": "Job Applicant", "applicant_name": "Clean Check", "email_id": "clean.check@example.com"}}' 2>&1 | tail -1 | cut -c1-200
log "done"
