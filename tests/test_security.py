# =============================================================================
# tests/test_security.py - sign-in, roles and form protection
# =============================================================================
# To check:
#   not signed in -> the sign-in page (pages) / 401 (API)
#   a form without the right token -> 403
#   a Reviewer cannot start a run -> 403; a Preparer can; only an Admin sees the activity log
#   windows mode: the name from the IIS header is used; a name not in USERS -> 403
#   downloads only come from the service's own output folders
