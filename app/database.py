"""
Database Connection & Session Management
Supports both Neon Serverless PostgreSQL (with SSL & connection pooling)
and local SQLite fallback for seamless execution.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from typing import Generator
from app.config import settings

# Determine database engine parameters based on database type
is_sqlite = settings.normalized_database_url.startswith("sqlite")

connect_args = {}
engine_kwargs = {}

if is_sqlite:
    # SQLite requires check_same_thread=False for FastAPI concurrency
    connect_args["check_same_thread"] = False
else:
    # Neon Serverless PostgreSQL connection pooling optimization
    # Prevents dropped connections when serverless instances scale or idle
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_recycle"] = 300
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20

# Create SQLAlchemy engine
engine = create_engine(
    settings.normalized_database_url,
    connect_args=connect_args,
    **engine_kwargs
)

# Create session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base model for ORM entities
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a clean transactional database session per request.
    Automatically closes session upon request completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initializes database tables defined in models.
    Called on application startup.
    """
    import app.models  # Ensure models are registered with Base
    Base.metadata.create_all(bind=engine)
