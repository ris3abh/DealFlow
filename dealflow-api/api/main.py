from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from api.core.config import settings
from api.routers import clients, conversations, usage
from api.core.client_manager import get_client_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for the application"""
    # Startup event
    client_manager = get_client_manager()
    await client_manager.initialize()
    yield
    # Shutdown event
    client_manager = get_client_manager()
    await client_manager.cleanup()

app = FastAPI(
    title="DealFlow API",
    description="API service for DealFlow sales conversation agents",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(clients.router, prefix="/api/clients", tags=["clients"])
app.include_router(conversations.router, prefix="/api/conversations", tags=["conversations"])
app.include_router(usage.router, prefix="/api/usage", tags=["usage"])

# Health check endpoint
@app.get("/api/health", tags=["health"])
async def health_check():
    """Check if the API is running"""
    return {"status": "ok"}