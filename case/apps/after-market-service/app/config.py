from pydantic_settings import BaseSettings
from functools import lru_cache
import yaml
from pathlib import Path


class Settings(BaseSettings):
    database: dict
    news_api: dict
    dingtalk: dict
    scheduler: dict
    app: dict

    class Config:
        extra = "allow"


@lru_cache()
def get_settings():
    config_path = Path(__file__).parent.parent / "config.yaml"
    with open(config_path, encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return Settings(**config)


settings = get_settings()
