# =============================================================================
# app/dependencies.py - the checks FastAPI runs before a route
# =============================================================================
# FastAPI calls these "dependencies": a route lists them, and FastAPI runs them first.
# What goes here:
#   current_user   WHO is asking: the session (choose mode) or the IIS header (windows mode).
#                  Not signed in -> the sign-in page (pages) or 401 (API)
#   role(...)      MAY they do this? Lets only reviewer / preparer / admin through - otherwise 403
#   check_csrf     the hidden form token must match the session - stops another website pressing Run
#   json_only      API calls that change something must be JSON - otherwise 415
#
# Used by: every route in routers/
# Requirements covered: R7, R8, R14
