import logging
import os
from fastapi import FastAPI
from contextlib import asynccontextmanager
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Server starting up -chromaDb running in-memory")
    yield
    logger.info("Server Shutting down")
    

app = FastAPI(title="Rag chatbot api", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware, 
    allow_origins = settings.allowed_orign_lists,
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"]
)

@app.get("/health")
async def health(): 
    return {"status": "ok"}