from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import auth, news
from app.core.config import settings
from app.core.error import setup_error_handlers
import logging

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.logging_level),
    format=settings.logging_format
)

app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 设置错误处理
setup_error_handlers(app)

# 注册路由
app.include_router(auth.router)
app.include_router(news.router)

@app.get("/")
def read_root():
    return {"message": "News API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
