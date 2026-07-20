import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from dashboard.backend.analytics.router import router as analytics_router
from dashboard.backend.auth.router import router as auth_router
from dashboard.backend.db.init_db import init_database
from dashboard.backend.platforms.router import router as platforms_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs("storage", exist_ok=True)
    await init_database()
    yield


app = FastAPI(title="Social Media Dashboard", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(analytics_router)
app.include_router(platforms_router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


# Serve frontend static files in production
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="spa")
