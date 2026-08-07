from __future__ import annotations

import logging
import sys


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s event=%(message)s",
        stream=sys.stdout,
    )
