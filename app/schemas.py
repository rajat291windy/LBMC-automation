# =============================================================================
# app/schemas.py - the shape of the data the API receives and returns
# =============================================================================
# Pydantic models. FastAPI checks every request and answer against them and shows them in /docs.
# What goes here:
#   MonthFolder      name, number of Journal Entry files, last run and its status
#   RunRequest       what POST /api/runs receives: month, dry_run
#   RunStarted       what it answers: run id, status, where to follow the run
#   LocationResult   one location: code, region, client, file, totals, status, issues, Excel link
#   RunResult        one run: month, who, when, status, counts, master file link
#   RunDetail        a run plus all its locations
# Amounts are text (e.g. "733846.98") so every cent stays exact.
#
# Requirements covered: R13 (the API)
