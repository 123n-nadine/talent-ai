#!/bin/bash
# Rebuild the dev demo from scratch: erase the engine data of this site, recreate the site with
# ERPNext + HRMS + Talent AI, run the setup and submit the 25 synthetic applicants (2017 through the
# real form in headless Chrome when the browser driver is available). Dev only, synthetic data.
set -euo pipefail
cd "$(dirname "$0")"
set -a; source .env; set +a
ROOT=$(cd .. && pwd)
KEY=$(grep '^TENANT_API_KEY=' "$ROOT/talent-engine/.env" | cut -d= -f2-)
API=http://127.0.0.1:18000
OPENING=HR-OPN-2026-0001
# 1. engine: erase this site's candidates (JA- references) and the demo job
refs=$(curl -s -H "Authorization: Bearer $KEY" "$API/v1/candidates?limit=1000" | python3 -c "import json,sys;d=json.load(sys.stdin);c=d.get('candidates',d) if isinstance(d,dict) else d;print(' '.join(x.get('ref') or x.get('external_ref') for x in c if str(x.get('ref') or x.get('external_ref')).startswith('JA-')))")
for r in $refs; do curl -s -o /dev/null -X DELETE -H "Authorization: Bearer $KEY" "$API/v1/candidates/$r"; done
for j in HR-OPN-2026-0001 HR-OPN-2026-0002; do curl -s -o /dev/null -X DELETE -H "Authorization: Bearer $KEY" "$API/v1/jobs/$j" || true; done
echo "engine: erased $(echo $refs | wc -w) candidates and job $OPENING"
# 2. site
docker compose exec -T bench bash -lc "cd ~/work/frappe-bench && bench new-site $SITE --force --db-root-password '$DB_ROOT_PASSWORD' --admin-password '$ADMIN_PASSWORD' --mariadb-user-host-login-scope='%' --install-app erpnext --install-app hrms --install-app ido_talent_ai > ~/new-site.log 2>&1 && bench --site $SITE set-config talent_ai_apply_limit 100 >/dev/null && bench --site $SITE enable-scheduler"
# 3. setup (arguments through stdin, never on the command line)
KEY="$KEY" python3 -c "
import json,os
print(json.dumps({'engine_url':'http://api:8000','api_key':os.environ['KEY'],'callback_url':'http://frappe:18050/api/method/ido_talent_ai.api.receive_result','passwords':{k:v for k,v in {'hr.manager@example.com':os.environ['HR_MANAGER_PASSWORD'],'hr.user@example.com':os.environ['HR_USER_PASSWORD'],'employee@example.com':os.environ['EMPLOYEE_PASSWORD'],'interviewer@example.com':os.environ.get('INTERVIEWER_PASSWORD'),'ess@example.com':os.environ.get('ESS_PASSWORD'),'sysmanager@example.com':os.environ.get('SYSTEM_MANAGER_PASSWORD'),'portal.applicant@example.com':os.environ.get('PORTAL_PASSWORD')}.items() if v}}))" \
  | docker compose exec -T bench bash -c 'umask 077; cat > /home/frappe/seed_args.json'
docker compose exec -T bench bash -lc 'cd ~/work/frappe-bench && bench --site '"$SITE"' execute ido_talent_ai.scripts.seed_demo.setup --kwargs "$(cat ~/seed_args.json)" | tail -1; rm -f ~/seed_args.json'
# 4. applicants: 2017 through the real form (optional), the rest through the same endpoint
SKIP=""
if [ -n "${FORM_DRIVER:-}" ] && [ -x "${FORM_PYTHON:-}" ]; then
  "$FORM_PYTHON" "$FORM_DRIVER" http://127.0.0.1:18050 "${FORM_SHOTS:-/tmp}" "$OPENING" 2017 && SKIP=2017
fi
python3 "$ROOT/ido_talent_ai/ido_talent_ai/scripts/submit_demo_applications.py" --url http://127.0.0.1:18050 --host "$SITE" \
  --opening "$OPENING" --cvs "$ROOT/talent-engine/data/cvs" --delay 1.5 --skip "$SKIP" | tail -2
# 5. wait for the AI, then the second opening (Jeddah), the talent-pool cases and the consent cases
#    (OPEN_QUESTIONS #20, #21), wait again, then a backup
wait_ai() {
  for i in $(seq 1 120); do
    n=$(docker compose exec -T bench bash -lc "cd ~/work/frappe-bench && bench --site $SITE mariadb -N -e \"select count(*) from \\\`tabJob Applicant\\\` where ai_status='Processing'\"" 2>/dev/null | tr -d '\r\n ')
    [ "$n" = "0" ] && break; sleep 10
  done
}
wait_ai
echo "processing done"
docker compose exec -T bench bash -lc "cd ~/work/frappe-bench && bench --site $SITE execute ido_talent_ai.scripts.seed_demo.second_opening | tail -1 && bench --site $SITE execute ido_talent_ai.scripts.seed_demo.pool_cases | tail -1 && bench --site $SITE execute ido_talent_ai.scripts.seed_demo.paper_cases | tail -1"
sleep 5
wait_ai
echo "consent cases done"
docker compose exec -T bench bash -lc "cd ~/work/frappe-bench && bench --site $SITE backup --with-files | tail -1"
