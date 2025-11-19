from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import init_db
from app.api import auth, documents, search, clustering
from app.worker import celery_app
from app.utils.init_data import ensure_default_admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        await init_db()
        print("Database initialized successfully")
        await ensure_default_admin()
    except Exception as e:
        print(f"Startup initialization error: {e}")
        # Don't fail startup if DB init fails
    yield
    # Shutdown
    pass


app = FastAPI(
    title="Qdrant CMS/DMS",
    description="Document Management System with Qdrant vector search backend",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(search.router)
app.include_router(clustering.router)


@app.get("/")
async def root():
    return {
        "message": "Welcome to Qdrant CMS/DMS API",
        "docs": "/docs",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
