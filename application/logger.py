import logging

from application.async_logger import AsyncHandler

logger = logging.getLogger("research_ai_agent")
logger.setLevel(logging.DEBUG)

if not logger.handlers:
    logger.addHandler(AsyncHandler())
    logger.propagate = False
