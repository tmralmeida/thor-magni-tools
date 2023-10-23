import logging
from typing import Any
from collections.abc import Mapping


class CustomFormatter(logging.Formatter):
    def __init__(
        self,
        fmt: str | None = None,
        datefmt: str | None = None,
        style="%",
        validate: bool = True,
        *,
        defaults: Mapping[str, Any] | None = None
    ) -> None:
        super().__init__(fmt, datefmt, style, validate, defaults=defaults)
        green = "\x1b[0;32m"
        grey = "\x1b[38;20m"
        orange = "\x1b[0;33m"
        red = "\x1b[31;20m"
        bold_red = "\x1b[31;1m"
        reset = "\x1b[0m"
        _format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"
        self.formats = {
            logging.DEBUG: grey + _format + reset,
            logging.INFO: green + _format + reset,
            logging.WARNING: orange + _format + reset,
            logging.ERROR: red + _format + reset,
            logging.CRITICAL: bold_red + _format + reset,
        }

    def format(self, record):
        log_fmt = self.formats.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)
