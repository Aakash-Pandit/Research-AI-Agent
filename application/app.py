from datetime import datetime

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
# from starlette.middleware.authentication import AuthenticationMiddleware

# from auth.backend import JWTAuthBackend
# from auth.dependencies import require_authenticated_user
# from database.db import drop_db, init_db

app = FastAPI(
    title="Reasearch AI Agent API",
    description="API for Reasearch AI",
    version="1.0.0",
    # dependencies=[Depends(require_authenticated_user)],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# app.add_middleware(AuthenticationMiddleware, backend=JWTAuthBackend())


@app.get("/")
async def root():
    return {
        "message": "Welcome to Reasearch AI Agent API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}