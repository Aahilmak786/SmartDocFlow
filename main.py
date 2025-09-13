from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
from dotenv import load_dotenv

from app.core.config import settings
from app.api.routes import documents, search, analysis, workflows
from app.core.database import init_db

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="SmartDocFlow API",
    description="Intelligent Document Processing & Analysis Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(documents.router, prefix="/api/v1/documents", tags=["documents"])
app.include_router(search.router, prefix="/api/v1/search", tags=["search"])
app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["analysis"])
app.include_router(workflows.router, prefix="/api/v1/workflows", tags=["workflows"])

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "SmartDocFlow API"}

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to SmartDocFlow API",
        "version": "1.0.0",
        "docs": "/docs"
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    await init_db()
    print("🚀 SmartDocFlow API started successfully!")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    print("🛑 SmartDocFlow API shutting down...")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

