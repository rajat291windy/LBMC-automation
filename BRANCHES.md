# Modules and branches

The service is built one **module** at a time. Every module has its **own branch**, is tested on that branch, and is merged into `main` through a pull request. `main` always holds the tested, working version.

## The modules, in build order

| # | Branch | Module (folder / files) | What it does | Needs | Done when |
|---|---|---|---|---|---|
| 1 | `feature/core-logic` | `app/engine/` – `pivot_je.py` (unchanged) + `core.py` | For one Journal Entry file: Debit/Credit, the **pivot table**, the **Summary JE**, the checks and the status, handed back as one result | – | `python -m tests.test_known_answers` and `python -m tests.test_core` pass |
| 2 | `feature/database` | `app/database/` | The 7 tables and every SQL statement: users, runs, results, activity log | – | A run with its locations can be saved and read back (tests) |
| 3 | `feature/month-folders` | `app/services/month_folders.py` | Month folders, their Journal Entry files, folders without one (C6) | 1 | The sample month shows its files and the MISSING folder |
| 4 | `feature/excel-outputs` | location workbook + `app/services/master_file.py` | The Excel file per location (pivot_je's layout) and the master file of a run | 1, 2 | The files open in Excel and their totals match the results |
| 5 | `feature/runner` | `app/services/runner.py` | A whole run: every location, dry run, one run per month, restart safety | 1–4 | `tests/test_runs.py` passes |
| 6 | `feature/api` | `app/schemas.py`, `app/dependencies.py`, `app/routers/api.py`, `app/main.py`, `app/config.py` | The JSON API and `/docs` | 5 | `tests/test_api.py` passes; a run can be started from `/docs` |
| 7 | `feature/web-pages` | `app/routers/auth.py`, `app/routers/pages.py`, `app/templates/`, `app/static/` | Sign-in, dashboard, Run button, results, downloads, roles | 6 | `tests/test_security.py` passes; the pages work in the browser |
| 8 | `feature/deployment` | `start_service.bat`, server settings, guides | Running on the LBMC server | 7 | The service runs on the server with Windows sign-in |

Build them in this order: each module only uses the ones above it.

## The steps for every branch

```
git checkout main
git pull
git checkout -b feature/core-logic          <- the branch of the module you work on
    ... write the module and its tests ...
python -m tests.test_known_answers           <- must pass on every branch
git add .
git commit -m "Core logic: pivot table and Summary JE for one file"
git push -u origin feature/core-logic
```

Then on GitHub: **Compare & pull request** → describe what the module does and how it was tested → someone reviews it → **Merge**. Back in VS Code:

```
git checkout main
git pull
git checkout -b feature/database             <- the next module starts from the updated main
```

## Rules

- One module per branch. Keep it small enough to review in one sitting.
- Always start a new branch from an up-to-date `main`.
- The tests of the module must pass before the pull request.
- Never change `app/engine/pivot_je.py` – the tested calculation. The other modules only call it.
- Never commit real LBMC files, the database, output files or passwords.
