# =============================================================================
# app/database/connection.py - opening the database
# =============================================================================
# What goes here:
#   connect()         open DB_PATH - foreign keys on, WAL mode so the pages can read while a run writes
#   create_tables()   the 7 tables, if they are not there yet:
#                       users          the 4 users and their roles
#                       rule_versions  the pivot_je SETTINGS used by each run
#                       runs           one row per click on Run
#                       run_locations  one row per location: totals, status, file fingerprint, Excel file
#                       check_results  one row per check per location
#                       account_lines  the pivot and the Summary JE lines of every location
#                       activity_log   sign-ins, runs and downloads
# One short connection per call: a SQLite connection belongs to the thread that opened it.
#
# Requirements covered: R10
