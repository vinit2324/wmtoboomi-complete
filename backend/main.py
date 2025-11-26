"""Main application"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.database import connect_to_mongodb, disconnect_from_mongodb, check_database_health
from app.routers import (
    customers_router,
    projects_router,
    conversions_router,
    mappings_router,
    ai_router,
    logs_router,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongodb()
    yield
    await disconnect_from_mongodb()

app = FastAPI(
    title="webMethods to Boomi Migration Accelerator",
    version="3.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:7200", "http://127.0.0.1:7200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    db_health = await check_database_health()
    return {"status": "healthy", "mongodb": db_health}

@app.get("/")
async def root():
    return {"service": "webMethods to Boomi Migration Accelerator", "version": "3.0.0"}

app.include_router(customers_router)
app.include_router(projects_router)
app.include_router(conversions_router)
app.include_router(mappings_router)
app.include_router(ai_router)
app.include_router(logs_router)
