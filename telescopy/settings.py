import os
import logging


def _to_bool(v):
    return str(v).lower()[:1] in ("t", "y", "1")


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

HTTP_PORT = 8000
BASE_HTTP_URL = f"http://192.168.5.50:{HTTP_PORT}/"

PUB_DIR = os.path.join(BASE_DIR, "pub")

GPHOTO_PATH = "gphoto2"
FOCUSER_IP = "192.168.5.51"

# PHD2_IP = '192.168.5.21'
PHD2_IP = "localhost"
PHD2_PORT = 4400

ENABLE_SIMULATORS = _to_bool(os.environ.get("ENABLE_SIMULATORS", True))

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "[%(asctime)s] %(levelname)s:%(name)s: %(message)s"},
    },
    "handlers": {
        "console": {
            "level": logging.DEBUG,
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "indi": {
            "level": logging.INFO,
            "class": "indi.logging.Handler",
            "router": None,
        },
    },
    "loggers": {"": {"level": logging.DEBUG, "handlers": ["console", "indi"],},},
}
