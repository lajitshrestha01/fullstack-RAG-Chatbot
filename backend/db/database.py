from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from config import settings

engine = create_async_engine(
    settings.DATABASE_URL, 
    pool_size=5, #safe default  limit for neon serverless 
    max_overflow=10, 
    pool_recycle=1800 #prevents unexpected disconnects from Neon idle  timeout
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine, 
    class_= AsyncSession, 
    expire_on_commit=False
)

class Base(DeclarativeBase):
    pass


async def get_db(): 
    async with AsyncSessionLocal as session: 
        try: 
            yield session
        
        finally: 
            await session.close()