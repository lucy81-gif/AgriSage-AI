# Project scripts

The main operational commands are module entry points from the repository root:

```powershell
python -m backend.app.db.init_db
python -m evaluations.run
```

The database initialiser is idempotent and the evaluation runner returns a
nonzero exit code when a scenario fails.
