"""
FastAPI backend for AquaAI - Marine Intelligence Assistant
Main application with /analyze, /chat, and /search endpoints
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from routers import analyze, chat, search
from schemas import AnalyzeResponse, ChatRequest, ChatResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AquaAI - Marine Intelligence",
    description="AI-powered marine species identification and reef health monitoring",
    version="1.0.0",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8080",
        "https://aquaai.vercel.app",
        "https://aquaai-frontend.vercel.app",
        # Add your exact Vercel URL below once deployed:
        # "https://YOUR-PROJECT-NAME.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(analyze.router)
app.include_router(chat.router)
app.include_router(search.router)


# ── Endpoints ─────────────────────────────────────────────────────────────────
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "AquaAI"}


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "service": "AquaAI - Marine Intelligence Assistant",
        "version": "1.0.0",
        "endpoints": {
            "POST /analyze": "Upload marine creature image for analysis",
            "POST /search":  "Search species by name",
            "POST /chat":    "Chat about identified species",
            "GET /health":   "Health check",
            "GET /docs":     "Swagger UI documentation",
            "GET /redoc":    "ReDoc documentation",
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )