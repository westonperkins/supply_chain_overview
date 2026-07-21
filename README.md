# AI Supply Chain Terminal

## Running the tests

The test suite runs against a frozen graph snapshot in
`backend/tests/fixtures/` — no live API, no network. Regenerate the snapshot
by copying the current data + config into that directory when the
underlying data changes.

```bash
# from repo root
cd backend
.venv/bin/python -m pytest -v tests/
```

To run the suite AND get the required report bundle (share-completeness
backlog, thin-bucket census, outbound sensitivity number, schema-gap
finding) printed together:

```bash
# from repo root
backend/.venv/bin/python -m tests.run_report
```

Reports are also written to `backend/tests/_out/` as individual `.txt`
files, one per data-completeness artefact.
