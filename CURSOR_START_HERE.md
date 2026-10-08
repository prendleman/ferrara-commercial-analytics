# Cursor start here — Ferrara Commercial Analytics

Independent synthetic interview demonstration for the Ferrara / Ferrero data and AI conversation. Work in this project.

Read `README.md`, `docs/CLIENT.md`, `docs/ASSISTANT_GAP.md`, and `docs/KNOWN_LIMITATIONS.md` first.

1. Run `python3 -m unittest discover -s tests -v`.
2. Start `python3 -m app.server` and walk Overview, Commercial, Analytics, Assistant, and Catalog.
3. Keep the synthetic banner visible. Every chart comes from `/api/metric`.
4. Call the assistant an approved-metric router. Do not call it a language model.
5. Leave refusals in place for syndicated share, IBP-style forecasts, and MDM / S/4.
6. Walk `docs/DEMO_SCRIPT.md` in under ten minutes.

Acceptance: tests pass, both logins show different net sales, a governed answer includes SQL and an audit row, and a Nielsen or IBP question returns no query.
