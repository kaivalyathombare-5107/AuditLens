"""
FastAPI main application with all routers
Location: backend/app/main.py
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.routers import auth, cases, documents, audit, tamper
from app.database import engine, Base

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create tables
Base.metadata.create_all(bind=engine)

# Initialize app
app = FastAPI(
    title="AuditLens Secure DMS",
    description="Secure Document Management System for Legal and Investigative Documents",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(cases.router)
app.include_router(documents.router)
app.include_router(audit.router)
app.include_router(tamper.router)  # NEW: Tamper detection routes


@app.get("/")
async def root():
    return {
        "message": "AuditLens Secure DMS API",
        "version": "2.0.0",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }


from datetime import datetime
