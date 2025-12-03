import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from fastapi import FastAPI
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from endpoints.api import auth, user, document, query, transaction

from utils.logger import get_logger
from endpoints.api import main_router

log = get_logger("MAIN")

app = FastAPI(
    title="GigaSchool RaaS API",
    description="REST API for RAG-based document query system with balance management",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(main_router, prefix="/api/v1")


@app.get("/")
def root():
    return {
        "message": "GigaSchool RAG API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        timeout_keep_alive=300,
        timeout_graceful_shutdown=30
    )