from pydantic_settings import BaseSettings
from typing import Optional
import yaml
import os

class Settings(BaseSettings):
    # 应用配置
    app_name: str = "News API"
    app_version: str = "1.0.0"
    app_description: str = "提供日、周、月新闻查询接口"
    
    # MongoDB配置
    mongodb_host: str = "localhost"
    mongodb_port: int = 27017
    mongodb_username: str = "admin"
    mongodb_password: str = "aa123aaqqA!@"
    mongodb_database: str = "news_db"
    mongodb_collection: str = "news"
    
    # JWT配置
    jwt_secret_key: str = "your-secret-key-here"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    
    # 认证配置
    auth_username: str = "admin"
    auth_password: str = "admin"
    
    # 日志配置
    logging_level: str = "INFO"
    logging_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

def load_config() -> Settings:
    """加载配置文件"""
    config_path = os.path.join(os.path.dirname(__file__), "..", "..", "config.yaml")
    
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)
        
        settings = Settings(
            app_name=config_data.get("app", {}).get("name", "News API"),
            app_version=config_data.get("app", {}).get("version", "1.0.0"),
            app_description=config_data.get("app", {}).get("description", "提供日、周、月新闻查询接口"),
            mongodb_host=config_data.get("mongodb", {}).get("host", "localhost"),
            mongodb_port=config_data.get("mongodb", {}).get("port", 27017),
            mongodb_database=config_data.get("mongodb", {}).get("database", "news_db"),
            mongodb_collection=config_data.get("mongodb", {}).get("collection", "news"),
            mongodb_username=config_data.get("mongodb", {}).get("username", ""),
            mongodb_password=config_data.get("mongodb", {}).get("password", ""),
            jwt_secret_key=config_data.get("jwt", {}).get("secret_key", "your-secret-key-here"),
            jwt_algorithm=config_data.get("jwt", {}).get("algorithm", "HS256"),
            jwt_access_token_expire_minutes=config_data.get("jwt", {}).get("access_token_expire_minutes", 30),
            auth_username=config_data.get("auth", {}).get("username", "admin"),
            auth_password=config_data.get("auth", {}).get("password", "admin"),
            logging_level=config_data.get("logging", {}).get("level", "INFO"),
            logging_format=config_data.get("logging", {}).get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
    else:
        settings = Settings()
    
    return settings

settings = load_config()
