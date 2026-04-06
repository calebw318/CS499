"""
audit_log.py
------------
Lightweight audit logging for the SPE research site.

Every login attempt (success or failure) and every logout is written to:
  - A rotating file:  logs/audit.log  (10 MB max, 5 backups kept)
  - Standard output   (so it appears in your terminal / deployment logs)

Each record is a single JSON line:
    {
      "timestamp": "2026-03-25T14:32:01.123456",
      "event":     "LOGIN_SUCCESS" | "LOGIN_FAILURE" | "LOGOUT",
      "username":  "jane.doe@uky.edu",
      "ip":        "123.45.67.89",
      "user_agent": "Mozilla/5.0 ..."
    }

Usage from app.py:
    from audit_log import log_login, log_logout
    log_login(username, request, success=True)
    log_logout(username, request)
"""

import json
import logging
import os
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler

# ---------------------------------------------------------------------------
# Logger setup
# ---------------------------------------------------------------------------

LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

_audit_logger = logging.getLogger("spe.audit")
_audit_logger.setLevel(logging.INFO)
_audit_logger.propagate = False   # don't double-print to Flask's root logger

# Rotating file handler — 10 MB per file, 5 backups
_file_handler = RotatingFileHandler(
    os.path.join(LOG_DIR, "audit.log"),
    maxBytes=10 * 1024 * 1024,
    backupCount=5,
    encoding="utf-8",
)
_file_handler.setFormatter(logging.Formatter("%(message)s"))
_audit_logger.addHandler(_file_handler)

# Console handler so events are visible during development
_console_handler = logging.StreamHandler()
_console_handler.setFormatter(logging.Formatter("[AUDIT] %(message)s"))
_audit_logger.addHandler(_console_handler)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_client_ip(flask_request) -> str:
    """
    Return the real client IP, honoring X-Forwarded-For if present.
    When running behind a reverse proxy (nginx, gunicorn), the actual
    client IP is in the first value of X-Forwarded-For.
    """
    forwarded_for = flask_request.headers.get("X-Forwarded-For", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return flask_request.remote_addr or "unknown"


def _write(event: str, username: str, flask_request, extra: dict = None) -> None:
    """Build a JSON record and write it to both sinks."""
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event":     event,
        "username":  username or "unknown",
        "ip":        _get_client_ip(flask_request),
        "user_agent": flask_request.headers.get("User-Agent", "unknown"),
    }
    if extra:
        record.update(extra)
    _audit_logger.info(json.dumps(record))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def log_login(username: str, flask_request, success: bool) -> None:
    """
    Record a login attempt.

    Parameters
    ----------
    username      : The username that was submitted.
    flask_request : The Flask `request` object for this HTTP request.
    success       : True if credentials were valid, False otherwise.
    """
    event = "LOGIN_SUCCESS" if success else "LOGIN_FAILURE"
    _write(event, username, flask_request)


def log_logout(username: str, flask_request) -> None:
    """
    Record a logout event.

    Parameters
    ----------
    username      : The username of the session being ended.
    flask_request : The Flask `request` object for this HTTP request.
    """
    _write("LOGOUT", username, flask_request)
