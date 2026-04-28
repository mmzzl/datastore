from pydantic_settings import BaseSettings
from typing import Optional
import yaml
import os
import logging
logger = logging.getLogger(__name__)

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
    mongodb_dbname: str = "news_db"  # 兼容旧代码
    mongodb_collection: str = "news"
    
    # JWT配置
    jwt_secret_key: str = "your-secret-key-here"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    
    # 认证配置
    auth_username: str = "admin"
    auth_password: str = "admin"
    
    # 盘后服务配置 (使用上面的mongodb配置)
    after_market_news_api_url: str = "http://life233.top"
    after_market_news_api_username: str = "admin"
    after_market_news_api_password: str = "admin"
    after_market_kline_api_url: str = "http://life233.top"
    after_market_dingtalk_webhook: str = ""
    after_market_dingtalk_secret: str = ""
    after_market_scheduler_time: str = "20:00"
    after_market_pre_cache_scheduler_time: str = "17:00"
    after_market_scheduler_timezone: str = "Asia/Shanghai"
    
    # 盯盘服务配置
    monitor_enabled: bool = True
    monitor_interval: int = 300  # 监控间隔（秒）
    monitor_scheduler_time: str = "09:30"  # 盯盘开始时间
    monitor_stocks: list = [
        {
            "code": "600519",
            "name": "贵州茅台",
            "hold": False,
            "buy_threshold": 0.05,
            "sell_threshold": 0.03,
            "cost_price": 0.0,
            "profit_target": 0.1,
            "stop_loss": 0.05
        },
        {
            "code": "000858",
            "name": "五粮液",
            "hold": False,
            "buy_threshold": 0.05,
            "sell_threshold": 0.03,
            "cost_price": 0.0,
            "profit_target": 0.1,
            "stop_loss": 0.05
        }
    ]
    
    # 日志配置
    logging_level: str = "INFO"
    logging_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging_file: str = "logs/app.log"
    logging_backup_count: int = 30  # 保留30天日志
    
    # LLM配置
    llm_provider: str = "deepseek"
    llm_api_key: str = ""
    llm_model: str = "deepseek-chat"
    llm_base_url: str = "https://api.deepseek.com"
    
    # 数据源配置 (akshare 或 tushare)
    data_source: str = "akshare"
    tushare_token: str = ""

    # Qlib 配置
    qlib_model_dir: str = "./models"
    qlib_min_sharpe_ratio: float = 1.5
    qlib_training_cron: str = "0 2 * * 0"
    qlib_risk_report_cron: str = "30 15 * * 1-5"
    qlib_provider_uri: str = "~/.qlib/qlib_data/cn_data"
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""
    celery_broker_url: Optional[str] = None
    celery_result_backend: Optional[str] = None

    # 备份配置
    backup_dir: str = "./backups"
    backup_retention_days: int = 30

    # 告警配置
    alert_dingtalk_webhook: str = ""
    alert_dingtalk_secret: str = ""
    alert_email_recipients: str = ""

    # 默认管理员配置
    default_admin_username: str = "admin"
    default_admin_password: str = "admin"
    default_user_password: str = "123456"

    class Config:
        env_file = ".env"
        case_sensitive = False

def load_config() -> Settings:
    """加载配置文件"""
    config_path = os.path.join(os.path.dirname(__file__), "..", "..", "config", "config.yaml")
    logger.info(f"Loading config from: {config_path}")
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
            mongodb_dbname=config_data.get("mongodb", {}).get("database", "news_db"),
            jwt_secret_key=config_data.get("jwt", {}).get("secret_key", "your-secret-key-here"),
            jwt_algorithm=config_data.get("jwt", {}).get("algorithm", "HS256"),
            jwt_access_token_expire_minutes=config_data.get("jwt", {}).get("access_token_expire_minutes", 30),
            auth_username=config_data.get("auth", {}).get("username", "admin"),
            auth_password=config_data.get("auth", {}).get("password", "admin"),
            logging_level=config_data.get("logging", {}).get("level", "INFO"),
            logging_format=config_data.get("logging", {}).get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
            logging_file=config_data.get("logging", {}).get("file", "logs/app.log"),
            logging_backup_count=config_data.get("logging", {}).get("backup_count", 30),
            llm_provider=config_data.get("llm", {}).get("provider", "deepseek"),
            llm_api_key=config_data.get("llm", {}).get("api_key", ""),
            llm_model=config_data.get("llm", {}).get("model", "deepseek-chat"),
            llm_base_url=config_data.get("llm", {}).get("base_url", "https://api.deepseek.com"),
            data_source=config_data.get("data_source", {}).get("provider", "akshare"),
            tushare_token=config_data.get("data_source", {}).get("tushare_token", ""),
            after_market_news_api_url=config_data.get("after_market", {}).get("news_api_url", "http://life233.top"),
            after_market_news_api_username=config_data.get("after_market", {}).get("news_api_username", "admin"),
            after_market_news_api_password=config_data.get("after_market", {}).get("news_api_password", "admin"),
            after_market_kline_api_url=config_data.get("after_market", {}).get("kline_api_url", "http://life233.top"),
            after_market_dingtalk_webhook=config_data.get("after_market", {}).get("dingtalk_webhook", ""),
            after_market_dingtalk_secret=config_data.get("after_market", {}).get("dingtalk_secret", ""),
            after_market_scheduler_time=config_data.get("after_market", {}).get("scheduler_time", "20:00"),
            after_market_pre_cache_scheduler_time=config_data.get("after_market", {}).get("pre_cache_scheduler_time", "17:00"),
            after_market_scheduler_timezone=config_data.get("after_market", {}).get("scheduler_timezone", "Asia/Shanghai"),
        monitor_enabled=config_data.get("monitor", {}).get("enabled", True),
        monitor_interval=config_data.get("monitor", {}).get("interval", 300),
        monitor_scheduler_time=config_data.get("monitor", {}).get("scheduler_time", "09:30"),
        monitor_stocks=config_data.get("monitor", {}).get("stocks", []),
        qlib_model_dir=config_data.get("qlib", {}).get("model_dir", "./models"),
        qlib_min_sharpe_ratio=config_data.get("qlib", {}).get("min_sharpe_ratio", 1.5),
        qlib_training_cron=config_data.get("qlib", {}).get("training_cron", "0 2 * * 0"),
        qlib_risk_report_cron=config_data.get("qlib", {}).get("risk_report_cron", "30 15 * * 1-5"),
        qlib_provider_uri=config_data.get("qlib", {}).get("provider_uri", "~/.qlib/qlib_data/cn_data"),
        backup_dir=config_data.get("backup", {}).get("dir", "./backups"),
        backup_retention_days=config_data.get("backup", {}).get("retention_days", 30),
        alert_dingtalk_webhook=config_data.get("alert", {}).get("dingtalk_webhook", ""),
        alert_dingtalk_secret=config_data.get("alert", {}).get("dingtalk_secret", ""),
        alert_email_recipients=config_data.get("alert", {}).get("email_recipients", ""),
    )
    else:
        settings = Settings()
    
    return settings

settings = load_config()
