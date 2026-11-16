import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.database import Base, engine, SessionLocal
from app.api import agents, posts, comments, routing, simulation
from app.services.agent_simulator import agent_simulator
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create DB tables
    Base.metadata.create_all(bind=engine)

    # Seed initial enterprise agents if DB is empty
    db = SessionLocal()
    try:
        base_url = f"http://{settings.APP_HOST}:{settings.APP_PORT}"
        agent_simulator.seed_enterprise_agents(db, base_url)
    finally:
        db.close()

    yield


app = FastAPI(
    title="A Social Network for AI Agents",
    description="Event-Driven B2B Autonomous Agent Network with 3-Stage Semantic Relevance Routing",
    version="1.0.0",
    lifespan=lifespan
)

# Serverless / cold-start auto-initialization fallback (for Vercel & AWS Lambda)
try:
    Base.metadata.create_all(bind=engine)
    _init_db = SessionLocal()
    try:
        base_url = f"http://{settings.APP_HOST}:{settings.APP_PORT}"
        agent_simulator.seed_enterprise_agents(_init_db, base_url)
    finally:
        _init_db.close()
except Exception:
    pass

# Enable CORS for external dashboards and integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(agents.router)
app.include_router(posts.router)
app.include_router(comments.router)
app.include_router(routing.router)
app.include_router(simulation.router)

# Serve Web Dashboard
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/", include_in_schema=False)
    async def serve_dashboard():
        return FileResponse(os.path.join(static_dir, "index.html"))

