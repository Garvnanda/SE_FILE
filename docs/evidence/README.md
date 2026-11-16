# Project evidence

- `pytest.xml` and `test-results.txt`: actual 20-case PostgreSQL test run.
- `browser-smoke.json`: 3 role sign-ins, dark/light views, 390px mobile document-overflow check, no browser page errors.
- `browser-admin.json`: administrator metadata editing was saved and verified, then the original name restored.
- `browser-demo.json`: canonical three-role order workflow through real forms, equity assertion, trade/order checks and admin refresh.
- PNG files: real rendered application views; `demo-result.png` shows actual canonical portfolio output.
- `environment.json`: actual Python/OS/PostgreSQL version and migration.
- `benchmark.json`: local sequential API measurement; not a production load test.
- `object-snapshot.json`: actual browser-demo instance data for an object diagram; no passwords/session data/email.
- `manifest.json`: SHA256 source snapshot; no fictional commit/tag.

Regenerate schema/API/runtime/source evidence with `.venv/Scripts/python.exe scripts/export_evidence.py` while the demo API runs. Browser scripts operate demonstration data; tests clear a separate database. No student identities, effort estimates, review signatures or experiment reports are asserted here.
