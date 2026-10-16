# dev-frappe

Local Docker-based Frappe bench used only to test `ido_talent_ai`. Compose project
`talentai-frappe`, ports 18050 (web) and 18051 (socket.io) on 127.0.0.1 and the Tailscale address;
MariaDB on 127.0.0.1:18052. Versions follow the client site: see `VERSIONS.md`.

- `setup.sh` builds the bench (frappe, erpnext, hrms pinned, our app linked read-only).
- `start.sh` is the container entry point: the dev database runs in memory (the server disk is a
  busy HDD, ~1.7 s per CREATE TABLE), so it restores the latest backup when the database is empty,
  keeps a backup every 2 hours, then runs `bench start`.
- `reset_demo.sh` rebuilds the demo from scratch: erases this site's data in the engine, recreates
  `talent.localhost` with ERPNext + HRMS + Talent AI, runs the setup (opening «مشرف أمن — الرياض»,
  approved profile, HR users) and submits the 25 synthetic applicants through the public form.
- `.env` (chmod 600, never committed) holds the database root password, the Administrator and HR
  user passwords and the Tailscale address.

Sites: `talent.localhost` (demo, default site) and `test.localhost` (automated tests:
`bench --site test.localhost run-tests --app ido_talent_ai --skip-before-tests`). Keep the
scheduler of `test.localhost` disabled (`bench --site test.localhost disable-scheduler`): its
safety nets would queue screenings of test applicants against an engine address nobody serves,
and those jobs fill the shared `long` queue ahead of the demo's.

The scripts here are committed; `.env` and the bench data never are.
