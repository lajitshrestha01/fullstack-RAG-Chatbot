from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    APP_ENV: str = "development"
    DEBUG: bool = False

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # OpenAI — embeddings + LLM
    OPENAI_API_KEY: str
    EMBED_MODEL: str = "text-embedding-3-small"
    
    #Groq -LLM inference 
    GROQ_API_KEY: str 
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"

   #postgress Neon database URL:
    DATABASE_URL: str
    DATABASE_URL_SYNC: str  # psycopg2 URL for alembic migrations

    # Upload limits
    MAX_UPLOAD_SIZE: int = 10_485_760   # 10MB
    MAX_PDF_PAGES: int = 50
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000,"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]


settings = Settings()
