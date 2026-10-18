#!/bin/bash
# (Re)create the automated-test site test.localhost (ERPNext + HRMS + Talent AI, scheduler off).
# The dev database lives in memory and start.sh restores only the demo site from its backup, so
# after a full stop/start of the stack the test site is gone until this runs again (round 10).
# Takes a few minutes. Dev only, synthetic data.
set -euo pipefail
cd "$(dirname "$0")"
set -a; source .env; set +a
TEST_SITE=test.localhost
docker compose exec -T bench bash -lc "cd ~/work/frappe-bench && bench new-site $TEST_SITE --force --db-root-password '$DB_ROOT_PASSWORD' --admin-password '$ADMIN_PASSWORD' --mariadb-user-host-login-scope='%' --install-app erpnext --install-app hrms --install-app ido_talent_ai > ~/new-test-site.log 2>&1 && bench --site $TEST_SITE disable-scheduler && bench --site $TEST_SITE set-config talent_ai_apply_limit 100 >/dev/null"
# the same setup as the demo (company through the setup wizard, HR users, settings): the tests
# need a company and the HR users; arguments through stdin, never on the command line
ROOT=$(cd .. && pwd)
KEY=$(grep '^TENANT_API_KEY=' "$ROOT/talent-engine/.env" | cut -d= -f2-)
KEY="$KEY" python3 -c "
import json,os
print(json.dumps({'engine_url':'http://api:8000','api_key':os.environ['KEY'],'callback_url':'http://frappe:18050/api/method/ido_talent_ai.api.receive_result','passwords':{k:v for k,v in {'hr.manager@example.com':os.environ['HR_MANAGER_PASSWORD'],'hr.user@example.com':os.environ['HR_USER_PASSWORD'],'employee@example.com':os.environ.get('EMPLOYEE_PASSWORD',''),'interviewer@example.com':os.environ.get('INTERVIEWER_PASSWORD',''),'ess@example.com':os.environ.get('ESS_PASSWORD',''),'sysmanager@example.com':os.environ.get('SYSTEM_MANAGER_PASSWORD',''),'portal.applicant@example.com':os.environ.get('PORTAL_PASSWORD','')}.items() if v}}))" \
  | docker compose exec -T bench bash -c 'umask 077; cat > /home/frappe/seed_args.json'
docker compose exec -T bench bash -lc 'cd ~/work/frappe-bench && bench --site '"$TEST_SITE"' execute ido_talent_ai.scripts.seed_demo.setup --kwargs "$(cat ~/seed_args.json)" | tail -1; rm -f ~/seed_args.json'
# one run without --skip-before-tests: the installed apps' before_tests hooks create the test
# company, warehouses and HR records the app tests need (then every run uses the skip flag)
docker compose exec -T bench bash -lc "cd ~/work/frappe-bench && bench --site $TEST_SITE run-tests --app ido_talent_ai 2>&1 | tail -3"
echo "test site $TEST_SITE ready (scheduler disabled, test records created)"
