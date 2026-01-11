"""
Configuration settings for the IDP system.
Loaded from environment variables with defaults for local development.
All settings must support offline, air-gapped deployment.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables.
    No secrets, no telemetry, no external services.
    """
    
    # Application
    APP_NAME: str = "IDP - Intelligent Document Processing"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 8000))
    API_PREFIX: str = "/api/v1"
    
    # File & Storage
    BASE_DIR: Path = Path(__file__).parent.parent
    UPLOAD_DIR: Path = Path(os.getenv("UPLOAD_DIR", "/tmp/idp_uploads"))
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", 50))
    MAX_UPLOAD_SIZE_BYTES: int = MAX_UPLOAD_SIZE_MB * 1024 * 1024
    
    # Supported file types
    ALLOWED_EXTENSIONS: set = {"pdf", "jpg", "jpeg", "png"}
    
    # OCR Configuration
    OCR_ENGINE: str = os.getenv("OCR_ENGINE", "tesseract")  # tesseract or paddleocr
    TESSERACT_PATH: Optional[str] = os.getenv("TESSERACT_PATH")
    OCR_LANGUAGE: str = os.getenv("OCR_LANGUAGE", "eng")
    OCR_TIMEOUT_SECONDS: int = int(os.getenv("OCR_TIMEOUT_SECONDS", 300))
    
    # Preprocessing
    DESKEW_ENABLED: bool = os.getenv("DESKEW_ENABLED", "true").lower() == "true"
    DENOISE_ENABLED: bool = os.getenv("DENOISE_ENABLED", "true").lower() == "true"
    BINARIZATION_ENABLED: bool = os.getenv("BINARIZATION_ENABLED", "true").lower() == "true"
    
    # LLM Configuration
    LLM_MODEL_PATH: str = os.getenv("LLM_MODEL_PATH", "/models/llama-7b.gguf")
    LLM_CONTEXT_TOKENS: int = int(os.getenv("LLM_CONTEXT_TOKENS", 2048))
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", 512))
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", 0.1))
    LLM_TOP_P: float = float(os.getenv("LLM_TOP_P", 0.95))
    LLM_N_THREADS: int = int(os.getenv("LLM_N_THREADS", os.cpu_count() or 4))
    LLM_TIMEOUT_SECONDS: int = int(os.getenv("LLM_TIMEOUT_SECONDS", 120))
    
    # Processing Pipeline
    ENABLE_OCR: bool = os.getenv("ENABLE_OCR", "true").lower() == "true"
    ENABLE_LAYOUT_ANALYSIS: bool = os.getenv("ENABLE_LAYOUT_ANALYSIS", "true").lower() == "true"
    ENABLE_LLM_EXTRACTION: bool = os.getenv("ENABLE_LLM_EXTRACTION", "true").lower() == "true"
    ENABLE_VALIDATION: bool = os.getenv("ENABLE_VALIDATION", "true").lower() == "true"
    
    # Layout Detection
    MIN_TEXT_BLOCK_HEIGHT: int = int(os.getenv("MIN_TEXT_BLOCK_HEIGHT", 10))
    MIN_TEXT_BLOCK_WIDTH: int = int(os.getenv("MIN_TEXT_BLOCK_WIDTH", 20))
    PROXIMITY_THRESHOLD: int = int(os.getenv("PROXIMITY_THRESHOLD", 15))
    TABLE_ROW_THRESHOLD: int = int(os.getenv("TABLE_ROW_THRESHOLD", 10))
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_SUPPRESS_SENSITIVE_DATA: bool = os.getenv("LOG_SUPPRESS_SENSITIVE_DATA", "true").lower() == "true"
    
    # Database (optional, for job tracking)
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")  # e.g., "sqlite:///./idp.db"
    
    # Validation
    MIN_OCR_CONFIDENCE: float = float(os.getenv("MIN_OCR_CONFIDENCE", 0.6))
    MIN_EXTRACTION_CONFIDENCE: float = float(os.getenv("MIN_EXTRACTION_CONFIDENCE", 0.7))
    
    class Config:
        """Pydantic config."""
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"


# Create uploads directory if it doesn't exist
def init_directories():
    """Initialize required directories."""
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


settings = Settings()
init_directories()
