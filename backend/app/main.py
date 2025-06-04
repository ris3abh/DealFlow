from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import agents, conversations

# Initialize FastAPI
app = FastAPI(
    title="DealFlow Agent API",
    description="API for DealFlow sales agent framework",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(agents.router, prefix="/agents", tags=["Agents"])
app.include_router(conversations.router, tags=["Conversations"])

@app.get("/", tags=["Health"])
def health_check():
    return {"status": "healthy", "version": "0.1.0"}