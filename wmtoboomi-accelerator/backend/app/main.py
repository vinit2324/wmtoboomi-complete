"""
webMethods to Boomi Migration Accelerator - FastAPI Backend

Enterprise platform for automating 80-90% of webMethods to Boomi migrations.
Built for Jade Global Inc.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time

from app.config import get_settings, init_upload_dir
from app.database import Database
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
    """Application lifespan manager."""
    # Startup
    print("🚀 Starting webMethods to Boomi Migration Accelerator...")
    
    # Initialize upload directory
    init_upload_dir()
    
    # Connect to MongoDB
    await Database.connect()
    
    print("✅ Application started successfully!")
    
    yield
    
    # Shutdown
    print("📤 Shutting down...")
    await Database.disconnect()


# Create FastAPI application
app = FastAPI(
    title="webMethods to Boomi Migration Accelerator",
    description="""
    Enterprise platform for automating webMethods to Boomi migrations.
    
    ## Features
    - Multi-customer management with encrypted credentials
    - webMethods package parsing (manifest.v3, node.ndf, flow.xml)
    - Flow verb analysis (MAP, BRANCH, LOOP, REPEAT, SEQUENCE, Try/Catch, EXIT)
    - wMPublic service tracking and conversion
    - Automated Boomi component generation
    - Boomi API integration for direct push
    - AI-powered migration assistance
    
    ## Built for Jade Global Inc.
    """,
    version="3.0.0",
    lifespan=lifespan,
)

# Configure CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "detail": f"Internal server error: {str(exc)}",
            "type": type(exc).__name__
        }
    )


# Include routers
app.include_router(customers_router)
app.include_router(projects_router)
app.include_router(conversions_router)
app.include_router(mappings_router)
app.include_router(ai_router)
app.include_router(logs_router)


# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "webMethods to Boomi Migration Accelerator",
        "version": "3.0.0"
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "webMethods to Boomi Migration Accelerator",
        "version": "3.0.0",
        "description": "Enterprise platform for automating webMethods to Boomi migrations",
        "company": "Jade Global Inc.",
        "documentation": "/docs",
        "health": "/api/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=True
    )
