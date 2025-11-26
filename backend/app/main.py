"""Main FastAPI application"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import customers, projects, conversions, integrations, logs, ai

app = FastAPI(
    title="webMethods to Boomi Migration Accelerator",
    description="Enterprise migration automation platform",
    version="3.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:7200", "http://127.0.0.1:7200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(customers.router)
app.include_router(projects.router)
app.include_router(conversions.router)
app.include_router(integrations.router)
app.include_router(logs.router)
app.include_router(ai.router)

@app.get("/")
async def root():
    return {
        "name": "webMethods to Boomi Migration Accelerator",
        "version": "3.0.0",
        "status": "running"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}
