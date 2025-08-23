from middleware.logging_middleware import logger
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from fastapi import Request

class ExceptionHandlingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            logger.error(f"Unhandled exception: {e}", exc_info=True)
            response = JSONResponse(
                status_code=500,
                content={"detail": "An internal server error occurred."}
            )
        origin = request.headers.get("Origin")
        if origin:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
        else:
            # For requests without Origin header, just allow all origins without credentials
            response.headers["Access-Control-Allow-Origin"] = "*"
            return response
