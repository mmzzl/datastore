import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.auth import verify_token as verify_custom_token
from app.core.security import security

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.exempt_paths = [
            "/api/login",
            "/api/health",
            "/api/auth/token",
            "/api/docs",
            "/api/redoc",
            "/api/openapi.json",
            "/api/stock/kline",
            "/api/stock/realtime",
            "/api/stock/list",
            "/api/stock/search",
        ]

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        # allow exempt paths
        if any(path.startswith(p) for p in self.exempt_paths):
            return await call_next(request)
        auth = request.headers.get("Authorization")
        if not auth or not auth.startswith("Bearer "):
            return JSONResponse({"detail": "Not authenticated"}, status_code=401)
        token = auth.split(" ", 1)[1]
        user = None
        try:
            # Try custom token first
            user = verify_custom_token(token)
        except Exception:
            user = None
        if not user:
            try:
                # Try JWT token
                payload = security.verify_token(token)
                if payload:
                    user = payload.get("sub")
            except Exception:
                pass
        if not user:
            return JSONResponse({"detail": "Invalid or expired token"}, status_code=403)
        # 这里不强制将 user 注入到请求中，后续端点仍依赖 get_current_user
        return await call_next(request)
