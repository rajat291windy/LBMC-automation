# =============================================================================
# app/routers/api.py - the JSON API (for other programs, and for /docs)
# =============================================================================
# Routes to add:
#   GET  /api/months           the month folders and their last run
#   POST /api/runs             start a run - JSON body {"month": ..., "dry_run": ...}
#                              202 started, 409 that month is already running, 404 unknown month
#   GET  /api/runs             the latest runs
#   GET  /api/runs/{run_id}    one run with every location
#
# Uses: schemas.py, dependencies.py (role, json_only), services/runner.py, database/repository.py
# Requirements covered: R13
