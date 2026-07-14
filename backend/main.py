import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from routers.document_router import router as document_router
from sqlalchemy import text
from db.database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app")

@asynccontextmanager
async def lifespan(_app: FastAPI):
    async with engine.connect() as conn: 
        await conn.execute(text('SELECT 1'))
    logger.info("Database connected")
    yield
    await engine.dispose()
    logger.info("Server Shutting down")


app = FastAPI(title="Rag chatbot api", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok"}

# app.include_router(document_router)

