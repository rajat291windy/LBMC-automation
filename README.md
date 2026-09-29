# Revenue JE service – FastAPI skeleton

This is the **empty structure** of the Revenue JE service. There is no code yet. Every file says in comments what will go in it and which requirement it covers, so you can fill it in one file at a time.

---

## 1. The folders and files

```
revenue_je_service/
│  README.md                  this guide
│  requirements.txt           the packages to install
│  start_service.bat          will start the service with a double-click
│  .gitignore                 files Git should not keep
│
├─ app/                       the service itself
│  │  main.py                 creates the FastAPI app and connects all the parts
│  │  config.py               settings: folders, sign-in mode, the 4 users, port
│  │  dependencies.py         checks run before a route: who is asking, their role, the form token
│  │  schemas.py              Pydantic models: what the API receives and returns
│  │
│  ├─ routers/                the web addresses, grouped by topic
│  │     auth.py              sign-in and sign-out
│  │     pages.py             the HTML pages and the Run button
│  │     api.py               the JSON API
│  │
│  ├─ services/               the work behind the addresses
│  │     month_folders.py     month folders, Journal Entry files, folders without one
│  │     runner.py            start a run, and process it in the background
│  │     master_file.py       the master workbook of a run
│  │
│  ├─ database/               SQLite
│  │     connection.py        open the database, create the 7 tables
│  │     repository.py        every SQL statement, one function each
│  │
│  ├─ engine/                 the calculation: copy your tested pivot_je.py here, unchanged
│  │
│  ├─ templates/              the HTML pages
│  │     base.html  signin.html  dashboard.html  run.html  location.html
│  │     history.html  activity.html  error.html
│  │
│  └─ static/
│        style.css            the look of the pages
│
├─ data/                      the month folders (dummy data only on your computer)
│     README.txt              how a month folder is laid out
├─ output/                    the Excel files of every run (made by the service)
│     README.txt              where each run saves its files
└─ tests/
      test_known_answers.py   the calculation still gives the demo numbers
      test_runs.py            runs, dry runs, one run per month, errors
      test_api.py             the API and its status codes
      test_security.py        sign-in, roles, form protection
```

The `__init__.py` files (in `app`, `routers`, `services`, `database`, `engine` and `tests`) make each folder a Python package. They stay empty.

---

## 2. How the parts work together

Each layer only talks to the layer below it:

```
 browser / other programs
          |
 routers/        which address? -> which page or answer        (pages.py, api.py, auth.py)
          |      before each route: dependencies.py checks who is asking and whether they may
          v
 services/       the work: find the files, run a month, write the master file
          |
     +----+-----------------+
     v                      v
 engine/pivot_je.py     database/repository.py -> SQLite
 (the calculation,      (every SQL statement)
  not changed)
```

- **routers** decide what to answer, but don't calculate or write SQL.
- **services** do the work, but don't know about web pages.
- **database** is the only place with SQL.
- **engine** is your tested calculation, called as it is.

This keeps each file small, easy to test, and easy to change without breaking the others.

---

## 3. The order to fill it in

Each module is built on its own Git branch - see **BRANCHES.md** for the branch names and the Git steps.

| Step | File(s) | Done when |
|---|---|---|
| 1 | Copy `pivot_je.py` into `app/engine/`; write `tests/test_known_answers.py` | 7003 = 733,846.98 and 44105 = 216,073.21 |
| 2 | `app/config.py` | Folders, sign-in mode and the 4 users are set |
| 3 | `app/database/connection.py`, `repository.py` | The 7 tables are created; a user can be saved and read back |
| 4 | `app/services/month_folders.py` | The sample month shows its Journal Entry files and the folder without one |
| 5 | `app/services/runner.py`, `master_file.py` | A run of the sample month saves every location, the Excel files and the master file |
| 6 | `app/schemas.py`, `app/dependencies.py` | The models and the checks exist |
| 7 | `app/routers/api.py`, then `app/main.py` | `/docs` shows the API, and a run can be started from there |
| 8 | `app/routers/auth.py`, `pages.py`, `templates/`, `static/style.css` | The pages work in the browser: sign in, Run, results, downloads |
| 9 | `tests/test_runs.py`, `test_api.py`, `test_security.py` | All tests pass |
| 10 | `start_service.bat` | A double-click starts the service |

Run `test_known_answers.py` after every step.

---

## 4. The requirements, and where each one lives

| # | Requirement | Files |
|---|---|---|
| R1 | One click runs every location of a month | `services/month_folders.py`, `services/runner.py`, `routers/pages.py` |
| R2 | The same calculation as the tested `pivot_je.py` | `engine/pivot_je.py` (unchanged), `services/runner.py` |
| R3 | A status for every location; one bad file never stops the run | `services/runner.py` |
| R4 | One Excel file per location plus a master file; nothing overwritten | `services/runner.py`, `services/master_file.py` |
| R5 | Check C6: folders without a Journal Entry file | `services/month_folders.py` |
| R6 | Dry run | `services/runner.py`, `routers/pages.py` |
| R7 | 4 users with roles: Reviewer, Preparer, Admin | `config.py`, `dependencies.py` |
| R8 | Windows sign-in on the server; a sign-in page for testing | `config.py`, `dependencies.py`, `routers/auth.py` |
| R9 | One run per month folder at a time | `database/repository.py`, `services/runner.py` |
| R10 | Run history and an audit trail | `database/` |
| R11 | A restart never leaves a run "running" | `main.py`, `database/repository.py` |
| R12 | Results on screen | `routers/pages.py`, `templates/` |
| R13 | A JSON API for other programs | `routers/api.py`, `schemas.py` |
| R14 | Safe by design: roles on the server, form token, JSON-only API writes, safe downloads, `?` in SQL, 127.0.0.1 only | `dependencies.py`, `main.py`, `database/repository.py` |

---

## 5. Rules while you build

- `app/engine/pivot_je.py` is never changed. The service only calls it.
- Only dummy data in `data/` on your computer. Real LBMC files stay inside LBMC.
- Run the tests after every step.
- The working version of every file is in the **pivot_je_fastapi** folder. Look there when you're stuck.
