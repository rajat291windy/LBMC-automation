# =============================================================================
# app/routers/auth.py - sign-in and sign-out
# =============================================================================
# Only used in "choose" mode. On the LBMC server Windows signs people in, so these return 404 there.
# Routes to add:
#   GET  /signin    the page with the 4 users to choose from
#   POST /signin    remember the chosen user in the session      (form token checked)
#   POST /signout   forget the user                              (form token checked)
#
# Uses: dependencies.py (check_csrf), database/repository.py (users, activity log), templates/signin.html
# Requirements covered: R8
