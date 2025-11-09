from __future__ import annotations

import os
import sys


# Ensure project root is importable in tests (so `service`/`vecdb` can be imported)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


