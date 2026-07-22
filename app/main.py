"""
Application entry point.

Run with: uvicorn app.main:app --reload
"""

import os
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

from app.config import settings
from app.api.v1.router import api_router

load_dotenv()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API for the university maintenance and service request management platform.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ============================================================================
# Middleware
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Exception Handlers
# ============================================================================


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation failed", "errors": exc.errors()},
    )


@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "A database error occurred"},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred"},
    )

# ============================================================================
# Routes
# ============================================================================


@app.get("/")
def root():
    return {"message": "CampusFix API"}


app.include_router(api_router, prefix="/api/v1")
