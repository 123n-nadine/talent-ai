#!/bin/bash
# Create dev-frappe/.env with random passwords (once). Never commit .env.
cd "$(dirname "$0")"
[ -f .env ] && { echo ".env exists, nothing changed"; exit 0; }
r() { python3 -c 'import secrets;print(secrets.token_urlsafe(18))'; }
umask 077
{
  echo "DB_ROOT_PASSWORD=$(r)"; echo "ADMIN_PASSWORD=$(r)"; echo "TAILSCALE_IP=${TAILSCALE_IP:-100.85.37.127}"
  echo "SITE=talent.localhost"; echo "HR_MANAGER_PASSWORD=$(r)"; echo "HR_USER_PASSWORD=$(r)"; echo "EMPLOYEE_PASSWORD=$(r)"
} > .env
echo "wrote .env (chmod 600)"
