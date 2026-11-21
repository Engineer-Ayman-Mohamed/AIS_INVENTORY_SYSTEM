"""
Main FastAPI Application Entrypoint
Accounting Information System (AIS): Inventory Management & Valuation System
Academic Year 2026-2027

This service operationalizes the core cycle of an AIS:
  Input -> Processing -> Output -> Control

Integrates with Neon Serverless PostgreSQL and serves an interactive,
fully responsive HTML5 single-user executive management dashboard.
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.config import settings
from app.database import init_db, get_db
from app.routers import dashboard, items, goods_in, goods_out, valuation, controls


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application Lifespan Context:
    Executes database table creation upon startup.
    """
    init_db()
    yield


app = FastAPI(
    title="AIS Inventory Management & Valuation System",
    description="""
    ## Accounting Information System (AIS) Mini-Project
    **Platform:** Web / HTML5 Responsive Single-User Application  
    **Database:** Neon Serverless PostgreSQL / Cloud Storage  
    **Containerization:** Docker Ready  
    
    ### Core Functional Modules:
    1. **Executive Dashboard**: Real-time KPI summaries, stock valuation, turnover, and visual metrics.
    2. **Item Master**: Inventory catalog management with unique SKU enforcement and deletion integrity controls.
    3. **Goods In (Purchases)**: Acquisition recording with automatic cost-layer creation and moving average updates.
    4. **Goods Out (Sales)**: Sales transactions with perpetual COGS calculation and negative inventory blocking.
    5. **Valuation Report Engine**: Toggle cost-flow assumptions (FIFO, WAC, LIFO) and systems (Perpetual vs Periodic).
    6. **Analysis & Internal Controls**: ABC classification, low-stock alerts, 2% reconciliation tolerance engine, and immutable audit logs.
    """,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# Enable CORS for seamless local and containerized access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(dashboard.router)
app.include_router(items.router)
app.include_router(goods_in.router)
app.include_router(goods_out.router)
app.include_router(valuation.router)
app.include_router(controls.router)

# Mount Static Files (HTML5 UI, CSS, JS)
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", include_in_schema=False)
def serve_index():
    """Serves the modern single-user HTML5 Executive Application."""
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "AIS Inventory System API is operational. Visit /docs for OpenAPI documentation."}


@app.get("/api/health", tags=["System Health"])
def health_check(db: Session = Depends(get_db)):
    """
    Verifies API and database connectivity.
    Reports active database engine (Neon PostgreSQL vs SQLite fallback).
    """
    db_type = "Neon PostgreSQL" if "postgresql" in settings.normalized_database_url else "Local SQLite"
    try:
        db.execute(text("SELECT 1"))
        db_status = "Connected"
    except Exception as e:
        db_status = f"Error: {str(e)}"

    return {
        "status": "Online",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "database_type": db_type,
        "database_status": db_status,
        "operator": settings.DEFAULT_OPERATOR
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
