# =============================================================================
# app/database/repository.py - every SQL statement, one function each
# =============================================================================
# Always with ? placeholders - never paste text into SQL.
# Users:     sync_users (make the table match config.USERS), get_user, record_sign_in
# Runs:      rule_version_for, open_run (BEGIN IMMEDIATE - the one-run-per-month rule),
#            set_output_folder, finish_run, fail_run, mark_interrupted_runs
# Results:   save_location (the location, its checks and its account lines in one transaction)
# Reading:   get_run, recent_runs, last_run_per_month, run_locations, location, checks,
#            failed_checks, account_lines, row_counts
# Audit:     log, activity
#
# Requirements covered: R9, R10, R11
