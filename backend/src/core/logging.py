import sys
from logging.config import dictConfig

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,

    "formatters": {
        "default": {
            "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        },
        "detailed": {
            "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s | %(request_id)s | %(user_id)s"
        },
    },

    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": sys.stdout,
        },
    },

    "root": {
        "level": "INFO",
        "handlers": ["console"],
    },
}


def setup_logging():
    dictConfig(LOGGING_CONFIG)