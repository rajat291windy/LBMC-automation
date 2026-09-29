# =============================================================================
# app/services/runner.py - one run of a month folder
# =============================================================================
# Two parts:
#   start_run(month, user, dry_run)   QUICK - called by the Run button and by POST /api/runs:
#                                       - is it a real month folder with Journal Entry files?
#                                       - record the rule version (the SETTINGS of pivot_je.py)
#                                       - open the run: one run per month folder - refused if one is going
#   process_run(run_id)               SLOW - runs in the background:
#                                       - pivot_je.process_file() for every file (the tested code, unchanged)
#                                       - turn its results into rows: checks, pivot lines, Summary JE lines
#                                       - save each location in one transaction (all of it or nothing)
#                                       - add every folder without a Journal Entry file as MISSING
#                                       - write the master file (not for a dry run)
#                                       - mark the run done - or failed, with the reason
# Dry run: the run works in a temporary folder that is deleted at the end, so no files are kept.
# One bad file never stops the run: it is saved as ERROR with the reason.
#
# Requirements covered: R1, R2, R3, R4, R6, R9
