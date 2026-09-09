"""ROLEWISE FastAPI backend — serves all data from MongoDB + Claude agent."""

import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db import connect_db, close_db
from routes.questions import router as questions_router
from routes.roles import router as roles_router
from routes.tracks import router as tracks_router
from routes.trends import router as trends_router
from routes.agent import router as agent_router
from routes.progress import router as progress_router

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    await connect_db()
    yield
    await close_db()


app = FastAPI(
    title="ROLEWISE API",
    description="Backend for ROLEWISE interview prep platform",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow Next.js dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount route modules
app.include_router(questions_router, prefix="/api/questions", tags=["Questions"])
app.include_router(roles_router, prefix="/api/roles", tags=["Roles"])
app.include_router(tracks_router, prefix="/api/tracks", tags=["Tracks"])
app.include_router(trends_router, prefix="/api/trends", tags=["Trends"])
app.include_router(agent_router, prefix="/api/agent", tags=["Agent"])
app.include_router(progress_router, prefix="/api/progress", tags=["Progress"])


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "rolewise-api"}
