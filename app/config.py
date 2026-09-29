# =============================================================================
# app/config.py - every setting in one place
# =============================================================================
# What goes here:
#   DATA_FOLDER      the folder that holds the month folders (data/ here, the shared drive on the server)
#   OUTPUT_FOLDER    where every run saves its Excel files (output/)
#   DB_PATH          the SQLite database file
#   SIGN_IN          "choose" on your own computer, "windows" on the LBMC server
#   USER_HEADER      the header in which IIS passes on the Windows user name
#   USERS            the 4 users: Windows user name, name shown on the pages, role
#                    (reviewer / preparer / admin)
#   HOST, PORT       127.0.0.1 and 8000 - only this computer (on the server: only IIS) can reach the service
#   SECRET_KEY_FILE  the key that signs the session cookie
#
# The business rules are NOT here: they stay in the SETTINGS of engine/pivot_je.py, the tested file.
#
# Requirements covered: R7 (4 users and roles), R8 (sign-in)
