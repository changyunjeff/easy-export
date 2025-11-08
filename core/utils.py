from __future__ import annotations

import os


def is_debug(mode: str|None = None):
    """
    If the mode is set to development, return True; otherwise, return False.
    """
    if mode is not None:
        return mode == "dev" or mode == "development"
    env = os.getenv("ENV", "dev").lower()
    return env == "dev" or env == "development"