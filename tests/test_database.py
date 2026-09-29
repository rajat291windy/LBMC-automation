"""
app/config.py - every setting of the service in one place
=========================================================
The business rules are NOT here: they stay in the SETTINGS block at the top of app/engine/pivot_je.py,
the tested file. Every run records which rules it used (the rule_versions table).

Requirements covered: R7 (4 users and roles), R8 (sign-in)
"""
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent          # the project folder (the one with README.md)

# -----------------------------------------------------------------------------
# Folders and the database file
# -----------------------------------------------------------------------------
# Every sub-folder of DATA_FOLDER is one month folder with its own Run button.
# On the LBMC server this becomes the folder on the shared drive, for example
#     DATA_FOLDER = Path(r"\\lbmc-server\Finance\Revenue - Power Query")
DATA_FOLDER = PROJECT / "data"

# Every run saves its Excel files in its own sub-folder:  output\<month>\<run id> <user>\
OUTPUT_FOLDER = PROJECT / "output"

# The SQLite database - one file, made automatically the first time. Never put it in Git
# (.gitignore already leaves out *.sqlite3).
DB_PATH = PROJECT / "revenue_je.sqlite3"

# -----------------------------------------------------------------------------
# Sign-in
# -----------------------------------------------------------------------------
# "choose"  - on your own computer: a sign-in page where you pick one of the USERS below.
# "windows" - on the LBMC server: IIS signs people in with their Windows account and passes the
#             user name on in the USER_HEADER header.
SIGN_IN = "choose"
USER_HEADER = "X-Remote-User"

# The 4 users: (Windows user name, name shown on the pages, role).
#   reviewer - sees every run and result, downloads the Excel files
#   preparer - everything a Reviewer can, plus starting a run
#   admin    - everything a Preparer can, plus the activity log
# Replace these examples with the 4 real Windows user names. A user taken off this list is
# switched off - their old runs stay in the history.
USERS = [
    ("admin.user", "Admin User", "admin"),
    ("preparer.one", "Preparer One", "preparer"),
    ("preparer.two", "Preparer Two", "preparer"),
    ("reviewer.one", "Reviewer One", "reviewer"),
]

# -----------------------------------------------------------------------------
# The web server
# -----------------------------------------------------------------------------
HOST = "127.0.0.1"          # only this computer can open the service (on the server: only IIS)
PORT = 8000                 # the service opens at http://127.0.0.1:8000

# The key that signs the sign-in cookie - made once, kept next to the project, never in Git
SECRET_KEY_FILE = PROJECT / ".secret_key"
