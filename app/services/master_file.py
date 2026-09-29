# =============================================================================
# app/services/master_file.py - the master workbook of a run
# =============================================================================
# "Revenue JE Summary - <month> - All Locations.xlsx", saved in the run's own output folder.
#   Status sheet             one row per location: region, client, file, lines, totals,
#                            13000/50005 difference, status, issues, Excel file - plus a total row
#   Summary JE lines sheet   every Summary JE line of every location
# Everything is read back from the database, so the master file matches the pages.
#
# Requirements covered: R4
