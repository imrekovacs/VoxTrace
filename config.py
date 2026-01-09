from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://voxtrace:voxtrace@localhost:5432/voxtrace"
    
    # Audio Storage
    audio_storage_path: str = "./audio_storage"
    
    # Model Configuration
    whisper_model: str = "base"
    vad_aggressiveness: int = 3
    
    # Speaker Recognition
    speaker_threshold: float = 0.75  # Similarity threshold for speaker identification
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
