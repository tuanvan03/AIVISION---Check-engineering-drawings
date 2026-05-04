from typing import Literal, Optional
from urllib.parse import quote_plus
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # App
    APP_ENV: Literal["development", "production"] = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    TIMEZONE: str = "Asia/Ho_Chi_Minh"
    
    # Auth
    AUTH_MODE: Literal["local", "oauth"] = "local"
    
    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 24
    
    # OAuth
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GITHUB_CLIENT_ID: Optional[str] = None
    GITHUB_CLIENT_SECRET: Optional[str] = None
    OAUTH_REDIRECT_BASE_URL: str = "http://localhost:8000"
    
    # MySQL
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "app_user"
    MYSQL_PASSWORD: str
    MYSQL_DATABASE: str = "drawing_checker"
    MYSQL_POOL_MIN: int = 5
    MYSQL_POOL_MAX: int = 20
    
    # Analysis
    MAX_CONCURRENT_TASKS: int = 5
    TASK_TIMEOUT_SECONDS: int = 300
    
    # OpenAI & External
    OPENAI_API_KEY: str
    CHROMA_DB_PATH: str = "./.chroma_db"
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    
    @property
    def database_url(self) -> str:
        # asyncmy supports caching_sha2_password (required for MySQL 8.4+)
        # quote_plus encodes special chars in password (e.g. @, #, %)
        password = quote_plus(self.MYSQL_PASSWORD)
        return f"mysql+asyncmy://{self.MYSQL_USER}:{password}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}?charset=utf8mb4"

settings = Settings()
