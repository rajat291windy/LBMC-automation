# =============================================================================
# tests/test_api.py - the API
# =============================================================================
# To check:
#   GET /api/months, GET /api/runs, GET /api/runs/{run_id}
#   POST /api/runs -> 202, then the run is done
#   409 when the month is already running, 404 for an unknown month,
#   415 when the request is not JSON, 422 when the body is wrong
