import logging
from logging import StreamHandler, Formatter
from logging.handlers import RotatingFileHandler
from typing import Optional
import os

try:
    # Typed import; runtime optional
    from core.schemas.configs import LoggingConfig
except Exception:  # pragma: no cover
    LoggingConfig = None  # type: ignore

def _ensure_dir_for_file(path: Optional[str]) -> None:
    if not path:
        return
    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)


def _level_from_string(level_str: str) -> int:
    mapping = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    return mapping.get(level_str.upper(), logging.INFO)


def setup_logging(logging_config: Optional["LoggingConfig"]) -> None:
    """
    Initialize logging from LoggingConfig.

    - Root logger: general application logs to console (optional) and file
    - 'access' logger: request access logs to separate file
    - Error handler: writes level >= ERROR to error file if provided
    """
    # Prevent duplicate handlers if re-initialized (e.g., in reload)
    root_logger = logging.getLogger()
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    # Basic formatter
    formatter = Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Defaults if no config provided
    level = logging.INFO
    console_enabled = True
    log_path = None
    access_log_path = None
    error_log_path = None

    if logging_config is not None:
        level = _level_from_string(getattr(logging_config, "level", "INFO"))
        console_enabled = bool(getattr(logging_config, "console_enabled", True))
        log_path = getattr(logging_config, "log_path", None)
        access_log_path = getattr(logging_config, "access_log_path", None)
        error_log_path = getattr(logging_config, "error_log_path", None)

    root_logger.setLevel(level)

    # Console handler
    if console_enabled:
        console_handler = StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # General app file handler
    if log_path:
        _ensure_dir_for_file(log_path)
        app_file_handler = RotatingFileHandler(log_path, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8")
        app_file_handler.setLevel(level)
        app_file_handler.setFormatter(formatter)
        root_logger.addHandler(app_file_handler)

    # Error file handler (only errors and above)
    if error_log_path:
        _ensure_dir_for_file(error_log_path)
        error_file_handler = RotatingFileHandler(error_log_path, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8")
        error_file_handler.setLevel(logging.ERROR)
        error_file_handler.setFormatter(formatter)
        root_logger.addHandler(error_file_handler)

    # Access logger configuration to a separate file
    access_logger = logging.getLogger("access")
    # Avoid propagating to root to prevent duplicate console/file writes unless no handler configured
    access_logger.propagate = False
    # Clear existing handlers (reload-safe)
    for handler in list(access_logger.handlers):
        access_logger.removeHandler(handler)
    access_logger.setLevel(logging.INFO)

    if access_log_path:
        _ensure_dir_for_file(access_log_path)
        access_file_handler = RotatingFileHandler(access_log_path, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8")
        access_file_handler.setLevel(logging.INFO)
        access_file_handler.setFormatter(formatter)
        access_logger.addHandler(access_file_handler)
    else:
        # Fallback to console so access logs are still visible
        if console_enabled:
            access_console_handler = StreamHandler()
            access_console_handler.setLevel(logging.INFO)
            access_console_handler.setFormatter(formatter)
            access_logger.addHandler(access_console_handler)