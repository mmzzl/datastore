from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging

logger = logging.getLogger(__name__)

async def http_exception_handler(request: Request, exc: Exception):
    """HTTP异常处理"""
    logger.error(f"HTTP异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "服务器内部错误"}
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """请求验证异常处理"""
    logger.error(f"请求验证异常: {exc}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()}
    )

def setup_error_handlers(app):
    """设置错误处理"""
    app.add_exception_handler(Exception, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
