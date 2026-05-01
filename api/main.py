"""
FastAPI Application - CodeCritic AI API

This module provides a REST API for the codebase chatbot functionality.
Run with: uvicorn api.main:app --reload --port 8000
"""
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import routers
from api.routes import chat, index, health

# Create FastAPI app
app = FastAPI(
    title="CodeCritic AI API",
    description="""
    A REST API for chatting with your codebase using RAG and agentic workflows.
    
    ## Features
    - **Index** codebases from GitHub URLs, local directories, or ZIP files
    - **Chat** with your codebase using natural language
    - **Agentic mode** for complex multi-step reasoning
    - **Graph-enhanced retrieval** using AST analysis
    
    ## Getting Started
    1. POST `/api/index` with your codebase source
    2. POST `/api/chat` with your questions
    
    ## Providers
    - **Gemini**: Google's Gemini 2.0 Flash (recommended)
    - **Groq**: Llama 3.3 70B (faster, lower quality)
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(index.router, prefix="/api", tags=["Indexing"])
app.include_router(chat.router, prefix="/api", tags=["Chat"])


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "CodeCritic AI API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health",
        "endpoints": {
            "index": "POST /api/index",
            "chat": "POST /api/chat",
            "health": "GET /api/health"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
