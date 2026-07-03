import logging
import sys
from datetime import datetime, timezone

from app.core.config import settings

logger = logging.getLogger("agrilend")
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))


class AuditLogger:
    def __init__(self):
        self.enabled = settings.audit_log_enabled

    async def log(
        self,
        action: str,
        user_id: str,
        resource: str,
        resource_id: str,
        details: str | None = None,
    ) -> None:
        if not self.enabled:
            return
        logger.info(
            "AUDIT | user=%s action=%s resource=%s resource_id=%s details=%s",
            user_id,
            action,
            resource,
            resource_id,
            details or "",
        )


audit_logger = AuditLogger()
