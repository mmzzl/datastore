from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # MongoDB配置
    MONGODB_URL: str = "mongodb://admin:aa123aaqqA!@127.0.0.1:27017"
    MONGODB_DB: str = "eastmoney_news"
    MONGODB_COLLECTION: str = "news"
    
    # JWT配置
    SECRET_KEY: str = "bcb8b7160371aa0514fcba286c8c9e774eb854a76ab0c3dc9332c0b32cd3d936531d629db54d80edbab74008c4c33ea21f5a1ed99295282de4d5517ee51bd76f"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    
    # API配置
    API_PREFIX: str = "/api"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
