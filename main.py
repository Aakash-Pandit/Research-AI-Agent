import os

import uvicorn

from application.app import app

from database.db import Base, engine

# Register route modules (must happen before server starts)
import auth.apis  # noqa: F401
import users.apis  # noqa: F401
import users.models  # noqa: F401  — registers models with Base

# Create DB tables
Base.metadata.create_all(bind=engine)

port = int(os.getenv("API_PORT", "8000"))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=port)