import json
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

# Handle SQLite vs PostgreSQL URL conventions
db_url = settings.DATABASE_URL

# On Vercel / AWS Lambda serverless environments, root is read-only. Fallback to /tmp if using relative SQLite
if (os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME")) and db_url.startswith("sqlite:///."):
    db_url = "sqlite:////tmp/agent_network.db"

connect_args = {}
if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(db_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency for yielding database sessions per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

