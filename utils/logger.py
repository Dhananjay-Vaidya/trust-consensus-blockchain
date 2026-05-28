from __future__ import annotations

import json
import logging
import sys
from datetime import datetime


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%H:%M:%S"
        ))
        logger.addHandler(handler)
    logger.setLevel(level)
    return logger


class JSONFileHandler(logging.Handler):
    """Writes one JSON object per line to a .jsonl file."""

    def __init__(self, filepath: str) -> None:
        super().__init__()
        self.fp = open(filepath, "a", encoding="utf-8")

    def emit(self, record: logging.LogRecord) -> None:
        obj: dict = {
            "ts": record.created,
            "level": record.levelname,
            "msg": record.getMessage(),
        }
        if hasattr(record, "extra"):
            obj.update(record.extra)
        self.fp.write(json.dumps(obj) + "\n")
        self.fp.flush()

    def close(self) -> None:
        self.fp.close()
        super().close()
