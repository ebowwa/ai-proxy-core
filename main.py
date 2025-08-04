"""
Minimal AI Proxy Service
A clean, reusable API proxy for AI services
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import completions, gemini_live
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(
    title="AI Proxy Core",
    description="Minimal, stateless AI service proxy",
    version="0.3.2"
)

# Configure CORS - allow all origins by default
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(completions.router, prefix="/api", tags=["completions"])
app.include_router(gemini_live.router, prefix="/api", tags=["gemini"])

@app.get("/")
async def root():
    return {
        "message": "AI Proxy Core",
        "endpoints": {
            "completions": "/api/chat/completions",
            "gemini_live": "/api/gemini/ws"
        }
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)