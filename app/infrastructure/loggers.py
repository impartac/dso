# loggers.py
import logging
from pathlib import Path

LOG_DIR = Path("./logs")
LOG_DIR.mkdir(exist_ok=True)

# --- общий логгер ---------------------------------
app_logger = logging.getLogger("app")
app_logger.setLevel(logging.DEBUG)
app_handler = logging.FileHandler(LOG_DIR / "app.log")
app_handler.setFormatter(
    logging.Formatter(
        "%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        "%Y-%m-%d %H:%M:%S",
    )
)
app_logger.addHandler(app_handler)

# --- аудит‑логгер --------------------------------
audit_logger = logging.getLogger("audit")
audit_logger.setLevel(logging.INFO)
audit_handler = logging.FileHandler(LOG_DIR / "audit.log")
audit_handler.setFormatter(
    logging.Formatter(
        "%(asctime)s | %(event)s | %(user_id)s | %(details)s",
        "%Y-%m-%d %H:%M:%S",
    )
)
audit_logger.addHandler(audit_handler)
