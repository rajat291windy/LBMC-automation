# =============================================================================
# app/services/month_folders.py - finding the files
# =============================================================================
# What goes here:
#   month_folders()     the sub-folders of DATA_FOLDER - one per month
#   month_path(name)    the folder of a month - only names from that list, never a path someone typed
#   journal_files()     the Journal Entry files of a month - pivot_je.find_files() (skips Vendor files
#                       and earlier outputs)
#   missing_folders()   folders that have exports but no Journal Entry file (check C6)
#   region_client()     region = the first folder under the month, client = the last folder
#
# Requirements covered: R1, R5
