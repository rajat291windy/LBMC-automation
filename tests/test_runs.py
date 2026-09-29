# =============================================================================
# tests/test_runs.py - runs
# =============================================================================
# To check (on a copy of the data folder, with its own database):
#   a real run: every location saved, the Excel files and the master file are made
#   a dry run: the same results, no files kept
#   one run per month: a second run of the same month is refused and names who started the first
#   a file that cannot be read -> ERROR, the other files still run
#   the same location twice -> "7003 (2)"
#   a folder without a Journal Entry file -> MISSING
#   a run cut off by a restart -> failed
