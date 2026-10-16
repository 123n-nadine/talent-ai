# UI tools (headless Chrome over CDP)

Used to render-test the Frappe screens, submit the public form like a browser and take the
screenshots in `docs/screenshots/`. Development only, against the local bench.

Run with the engine's virtualenv (it has `websockets`):

    PY=talent-engine/.venv/bin/python
    $PY tools/ui/apply_via_form.py http://127.0.0.1:18050 /tmp/shots HR-OPN-2026-0001 2017 talent-engine/data/cvs
    $PY tools/ui/desk_shots.py http://127.0.0.1:18050 /tmp/shots hr.manager@example.com "$HR_MANAGER_PASSWORD"
    $PY tools/ui/acceptance.py ...   # phase 7 evidence (see docs/ACCEPTANCE_REPORT.md)

Chrome: `/opt/google/chrome/chrome` (already on the server). Debug port 18091–18099 on 127.0.0.1 only.
