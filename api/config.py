"""
Streamlined configuration for OpenRouter-based Echoes backend.
"""
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import List
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # ============================================
    # Server Configuration
    # ============================================
    port: int = Field(default=8000, env="PORT")
    host: str = Field(default="0.0.0.0", env="HOST")
    reload: bool = Field(default=True, env="RELOAD")
    
    # CORS Configuration
    allowed_origins: str = Field(default="*", env="ALLOWED_ORIGINS")
    
    @property
    def cors_origins(self) -> List[str]:
        """Parse allowed origins into a list."""
        if self.allowed_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.allowed_origins.split(",")]
    
    # ============================================
    # OpenRouter Configuration
    # ============================================
    openrouter_api_key: str = Field(..., env="OPENROUTER_API_KEY")
    openrouter_model: str = Field(
        default="qwen/qwen-2.5-72b-instruct",
        env="OPENROUTER_MODEL"
    )
    openrouter_site_url: str = Field(
        default="https://echoes-app.local",
        env="OPENROUTER_SITE_URL"
    )
    openrouter_app_name: str = Field(
        default="Echoes-Backend",
        env="OPENROUTER_APP_NAME"
    )
    
    # API behavior settings
    llm_temperature: float = Field(default=0.7, env="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(default=2000, env="LLM_MAX_TOKENS")
    llm_timeout: int = Field(default=60, env="LLM_TIMEOUT")
    llm_max_retries: int = Field(default=3, env="LLM_MAX_RETRIES")
    
    @field_validator("openrouter_api_key")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        """Validate OpenRouter API key format."""
        if not v or len(v) < 10:
            raise ValueError("Invalid OpenRouter API key")
        if not v.startswith("sk-or-v1-"):
            raise ValueError("OpenRouter API key should start with 'sk-or-v1-'")
        return v
    
    # ============================================
    # Sentence Transformer Model
    # ============================================
    sentence_transformer_model: str = Field(
        default="paraphrase-MiniLM-L6-v2",
        env="SENTENCE_TRANSFORMER_MODEL"
    )
    
    # ============================================
    # Data Paths
    # ============================================
    embeddings_dir: str = Field(default="embeddings", env="EMBEDDINGS_DIR")
    data_dir: str = Field(default="data", env="DATA_DIR")
    
    # ============================================
    # Logging
    # ============================================
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="logs/echoes.log", env="LOG_FILE")
    
    # ============================================
    # Feature Flags
    # ============================================
    use_llm_etymology: bool = Field(default=True, env="USE_LLM_ETYMOLOGY")
    cache_llm_responses: bool = Field(default=True, env="CACHE_LLM_RESPONSES")
    
    # ============================================
    # Constants
    # ============================================
    DEFAULT_TOP_N: int = 6
    MAX_TOP_N: int = 50
    DEFAULT_EXAMPLES_PER_ERA: int = 5
    MAX_EXAMPLES_PER_ERA: int = 20
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    # ============================================
    # Path Properties
    # ============================================
    @property
    def embeddings_path(self) -> Path:
        return Path(self.embeddings_dir)
    
    @property
    def data_path(self) -> Path:
        return Path(self.data_dir)
    
    @property
    def log_path(self) -> Path:
        return Path(self.log_file)
    
    def ensure_directories(self):
        """Create necessary directories if they don't exist."""
        self.embeddings_path.mkdir(parents=True, exist_ok=True)
        self.data_path.mkdir(parents=True, exist_ok=True)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()

# Ensure directories exist on import
settings.ensure_directories()