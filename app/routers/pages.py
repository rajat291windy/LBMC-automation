# =============================================================================
# app/routers/pages.py - the HTML pages
# =============================================================================
# Routes to add:
#   GET  /                                       dashboard: month folders, Run button + Dry run tick box,
#                                                recent runs
#   POST /runs                                   the Run button: Preparer or Admin, form token checked.
#                                                Opens the run, starts the slow part in the background,
#                                                answers 303 -> the run page
#   GET  /runs/{run_id}                          run page: live progress (refreshes every 2 seconds),
#                                                counts, downloads, every location
#   GET  /runs/{run_id}/locations/{code}         location page: checks, pivot, Summary JE
#   GET  /runs/{run_id}/master                   download the master file
#   GET  /runs/{run_id}/locations/{code}/excel   download a location's Excel file
#   GET  /history                                every run
#   GET  /activity                               the activity log (Admin only)
#
# Uses: templates/, dependencies.py, services/runner.py, services/month_folders.py, database/repository.py
# Requirements covered: R1, R6, R9, R12
