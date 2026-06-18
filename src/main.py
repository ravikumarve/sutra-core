"""
SUTRA Core - FastAPI Application
Main application entry point
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import uvicorn

from src.config.settings import settings
from src.db.connection import db_manager
from src.api.routes import health, auth, webhooks, agents, tenants, dashboard, inventory, customers, orders
from src.api.middleware.security import SecurityMiddleware
from src.api.middleware.validation import ValidationMiddleware
from src.api.middleware.rate_limit import RateLimitMiddleware
from src.security.enhancements import SecurityHeadersMiddleware
from src.agents.coordinator import agent_coordinator

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    Handles startup and shutdown events
    """
    # Startup
    logger.info("Starting SUTRA Core application...")
    
    # Initialize database engine
    try:
        db_manager.create_engine()
        logger.info("Database engine initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database engine: {e}")
        raise
    
    # Initialize agent coordinator (optional in development mode)
    try:
        await agent_coordinator.start()
        logger.info("Agent coordinator started successfully")
    except Exception as e:
        if settings.is_development:
            logger.warning(f"Failed to start agent coordinator in development mode: {e}")
            logger.warning("Application will continue without agent coordinator")
        else:
            logger.error(f"Failed to start agent coordinator: {e}")
            raise
    
    logger.info("SUTRA Core application started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down SUTRA Core application...")
    
    # Stop agent coordinator (if it was started)
    try:
        await agent_coordinator.stop()
        logger.info("Agent coordinator stopped successfully")
    except Exception as e:
        logger.error(f"Failed to stop agent coordinator: {e}")
    
    logger.info("SUTRA Core application shut down successfully")


# Create FastAPI application
app = FastAPI(
    title="SUTRA Core",
    description="Multi-agent WhatsApp business automation system",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Add GZip middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add custom middleware
app.add_middleware(SecurityMiddleware)
app.add_middleware(ValidationMiddleware)
app.add_middleware(RateLimitMiddleware)


# Exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation exceptions"""
    return JSONResponse(
        status_code=422,
        content={
            "error": True,
            "message": "Validation error",
            "details": exc.errors(),
            "status_code": 422
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "Internal server error",
            "status_code": 500
        }
    )


# Include routers
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["Webhooks"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["Agents"])
app.include_router(tenants.router, prefix="/api/v1/tenants", tags=["Tenants"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])
app.include_router(inventory.router, prefix="/api/v1/inventory", tags=["Inventory"])
app.include_router(customers.router, prefix="/api/v1/customers", tags=["Customers"])
app.include_router(orders.router, prefix="/api/v1/orders", tags=["Orders"])


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "SUTRA Core",
        "version": "1.0.0",
        "status": "running",
        "environment": settings.environment
    }


def main():
    """Main entry point"""
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        workers=settings.workers,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )


if __name__ == "__main__":
    main()