# First message to paste into Claude Code (on the server)

Open this folder in VS Code (Remote SSH), start Claude Code in it, and paste:

---

اقرا `CLAUDE.md` كله، وبعده `docs/ARCHITECTURE.md` و `docs/PLAN.md` و `docs/TESTING.md` و `docs/DEPLOY_CHECKLIST.md`، وبص على الملفات اللي في `reference/` (افتح `reference/demo/README.md` و `reference/discovery/00_SUMMARY.md` و `reference/discovery/08_gap_analysis.md`).

Then:
1. Summarise back to me in simple Egyptian Arabic, in 10 lines max, what we are building and the rules you must follow on this shared server.
2. List anything in the docs that is unclear or contradicts itself.
3. Start **Phase 0 only** from `docs/PLAN.md`. It is read-only first: inspect the server and write `docs/SERVER_REPORT.md`. Do not install anything, do not pull images, do not use sudo.
4. Stop after Phase 0 and wait for my OK.

---

For every next session:

> اقرا `CLAUDE.md` وشوف الـ Status، وكمّل المرحلة اللي عليها الدور في `docs/PLAN.md`، ووقف في آخرها.
