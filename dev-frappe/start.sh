#!/bin/bash
# Bench container entry point: restore the dev site from its latest backup when the in-memory
# database is empty (after a container or server restart), then run the bench.
cd /home/frappe/work/frappe-bench 2>/dev/null || exec sleep infinity
SITE="${SITE:-talent.localhost}"
CONF="sites/$SITE/site_config.json"
if [ -f "$CONF" ]; then
  DB_NAME=$(python3 -c "import json;print(json.load(open('$CONF'))['db_name'])")
  for i in $(seq 1 60); do mariadb -h mariadb -uroot -p"$DB_ROOT_PASSWORD" -e "select 1" >/dev/null 2>&1 && break; sleep 2; done
  if ! mariadb -h mariadb -uroot -p"$DB_ROOT_PASSWORD" -e "use \`$DB_NAME\`; select 1 from tabDefaultValue limit 1" >/dev/null 2>&1; then
    DB=$(ls -t sites/$SITE/private/backups/*-database.sql.gz 2>/dev/null | head -1)
    if [ -n "$DB" ]; then
      echo "[start.sh] database $DB_NAME is empty: restoring $DB"
      PRIV=$(ls -t sites/$SITE/private/backups/*-private-files.tar 2>/dev/null | head -1)
      PUB=$(ls -t sites/$SITE/private/backups/*-files.tar 2>/dev/null | grep -v private | head -1)
      bench --site "$SITE" restore "$DB" --db-root-password "$DB_ROOT_PASSWORD" \
        ${PRIV:+--with-private-files "$PRIV"} ${PUB:+--with-public-files "$PUB"} --force || echo "[start.sh] restore failed"
    else
      echo "[start.sh] database $DB_NAME is empty and there is no backup: run setup again"
    fi
  fi
fi
# the database lives in memory: keep a fresh backup on disk every 2 hours (Frappe keeps the last 3)
( while sleep 7200; do bench --site "$SITE" backup --with-files >/dev/null 2>&1; done ) &
exec bench start
