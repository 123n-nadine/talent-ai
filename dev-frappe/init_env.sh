#!/bin/bash
# Create dev-frappe/.env with random passwords (once). Never commit .env.
cd "$(dirname "$0")"
r() { python3 -c 'import secrets;print(secrets.token_urlsafe(18))'; }
umask 077
# passwords of the extra test users (permission checks); added to an existing .env when missing
EXTRA="INTERVIEWER_PASSWORD ESS_PASSWORD SYSTEM_MANAGER_PASSWORD PORTAL_PASSWORD"
if [ -f .env ]; then
  n=0; for k in $EXTRA; do grep -q "^$k=" .env || { echo "$k=$(r)" >> .env; n=$((n+1)); }; done
  echo ".env exists; added $n missing key(s), nothing else changed"; exit 0
fi
{
  echo "DB_ROOT_PASSWORD=$(r)"; echo "ADMIN_PASSWORD=$(r)"; echo "TAILSCALE_IP=${TAILSCALE_IP:-100.85.37.127}"
  echo "SITE=talent.localhost"; echo "HR_MANAGER_PASSWORD=$(r)"; echo "HR_USER_PASSWORD=$(r)"; echo "EMPLOYEE_PASSWORD=$(r)"
  for k in $EXTRA; do echo "$k=$(r)"; done
} > .env
echo "wrote .env (chmod 600)"
