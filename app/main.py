# =============================================================================
# app/main.py - the starting point of the service
# =============================================================================
# What goes here, in this order:
#   1. Create the FastAPI app (title, description) with its start-up steps ("lifespan"):
#        - create the database tables                     -> database/connection.py
#        - copy the 4 users from config.py into the users table -> database/repository.py
#        - mark runs that were cut off by a restart as failed
#   2. Add the session middleware: it remembers who signed in and the form token
#   3. Serve the static folder (style.css) and set up the templates folder
#   4. Include the routers: routers/auth.py, routers/pages.py, routers/api.py
#   5. Error handling: API errors stay JSON, page errors show templates/error.html
#   6. At the bottom: start Uvicorn when this file is run directly (the Run button in VS Code)
#
# Requirements covered: R11 (restart safety), R14 (security settings)
