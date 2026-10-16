# Versions of the local bench (built 2026-10-16)

| Component | Version | Commit | Date |
|---|---|---|---|
| frappe | v16.31.0 | 6a329d068416 | 2026-08-11 |
| erpnext | v16.32.0 | 81a6f97566b8 | 2026-08-11 |
| hrms | develop (no tag; `git describe`: assets-version-16-462) | 640af1592a01 | 2026-08-11 |
| Python | 3.14.8 | | |
| Node | 24.22.0 | | |
| MariaDB | 11.8 (in memory, see docker-compose.yml) | | |
| Image | frappe/bench:v5.31.0 | | |

HRMS develop declares `frappe>=17`; bench only warns. The commit of the same day as frappe
v16.31.0 is used (the client demo runs HRMS 17.0.0-dev on Frappe 16).
