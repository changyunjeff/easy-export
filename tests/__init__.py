from __future__ import annotations

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure project root is importable in tests (so `service`/`vecdb` can be imported)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 加载 .env 文件，从项目根目录加载
env_path = Path(__file__).parent.parent / ".env"
if not env_path.exists():
    env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"Loaded .env file from: {env_path}")
else:
    # 如果都不存在，尝试从当前工作目录加载（默认行为）
    load_dotenv()
    print("No .env file found in project root or tests directory, using default load_dotenv()")
