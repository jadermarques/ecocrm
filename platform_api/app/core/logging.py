import logging
import sys
from app.core.config import settings

def setup_logging():
    """
    Configures structured logging for the application.
    """
    log_level = logging.DEBUG if settings.APP_ENV == "local" else logging.INFO
    
    # Root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Console handler with structured format (simplified for now, can be JSON in prod)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    
    # Format
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)

    # Avoid duplicate handlers
    if not logger.handlers:
        logger.addHandler(handler)

    # Set specific log levels for libraries to avoid noise
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
