"""Centralized logging configuration for all microservices."""
import logging
import sys
from typing import Optional
import json
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "service": getattr(record, "service", "unknown"),
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, "extra_data"):
            log_data["data"] = record.extra_data
        
        return json.dumps(log_data)


def setup_logging(
    service_name: str,
    level: str = "INFO",
    json_format: bool = False,
    log_file: Optional[str] = None,
) -> logging.Logger:
    """
    Setup logging for a microservice.
    
    Args:
        service_name: Name of the service for identification
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Use JSON format for structured logging
        log_file: Optional file path for file logging
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(service_name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    
    if json_format:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Add service name to all log records
    old_factory = logging.getLogRecordFactory()
    
    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.service = service_name
        return record
    
    logging.setLogRecordFactory(record_factory)
    
    return logger


class LoggerAdapter(logging.LoggerAdapter):
    """Logger adapter for adding context to log messages."""
    
    def process(self, msg, kwargs):
        # Add extra context to message
        extra_data = self.extra.copy() if self.extra else {}
        if "extra" in kwargs:
            extra_data.update(kwargs.pop("extra"))
        
        kwargs["extra"] = {"extra_data": extra_data}
        return msg, kwargs


def get_logger(name: str, context: Optional[dict] = None) -> logging.Logger:
    """
    Get a logger with optional context.
    
    Args:
        name: Logger name
        context: Optional context dictionary to add to all log messages
    
    Returns:
        Logger or LoggerAdapter instance
    """
    logger = logging.getLogger(name)
    
    if context:
        return LoggerAdapter(logger, context)
    
    return logger
