
import os 
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings): 
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env"
        env_file_encoding="utf-8"
        extra="ignore"
        )
    
    #APP 
    APP_ENV: str = "development"
    DEBUG: bool = False
    
    #server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKER: int = 1
    
    #nvidia embeddings 
    
    NVIDIA_API_KEY: str
    NVIDIA_EMBED_MODEL: str = "nvidia/nv-embedcode-7b-v1"
    NVIDIA_BASE_URL: str = "https://integrate.api.nvidia.com/v1"
    
    #groq
    GROQ_API_KEY: str 
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"



    