import logging
from logging.handlers import RotatingFileHandler
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

# Configure logging
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
log_file = 'app.log'

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create a rotating file handler
file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=5)
file_handler.setFormatter(logging.Formatter(log_format))

# Add the file handler to the logger
logger.addHandler(file_handler)

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Log request information
        logger.info(f"Request: {request.method} {request.url} - Headers: {request.headers}")

        # Process the request
        response = await call_next(request)

        # Log response information
        logger.info(f"Response: {request.method} {request.url} - Status Code: {response.status_code}")

        return response