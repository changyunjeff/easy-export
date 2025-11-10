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

# 加载 config.test.yaml 文件（测试配置）
# 设置环境变量为 test，确保加载测试配置文件
os.environ.setdefault("ENV", "test")

# 导入配置加载函数
from core.config import load_config

# 确保加载测试配置文件
try:
    config_path = Path(__file__).parent.parent / "config.test.yaml"
    if config_path.exists():
        # 直接加载测试配置文件并设置全局配置
        import core.config as config_module
        # 强制重新加载测试配置
        config_module._global_config = None  # 清除缓存
        config_module._global_config = load_config(str(config_path))
        print(f"[OK] Loaded test config from: {config_path}")
        print(f"   Rate limit: {config_module._global_config.rate_limit.requests_per_minute}/min, "
              f"{config_module._global_config.rate_limit.requests_per_hour}/hour, "
              f"{config_module._global_config.rate_limit.requests_per_day}/day")
        print(f"   DDoS protection: {config_module._global_config.ddos_protection.max_requests_per_second}/sec, "
              f"{config_module._global_config.ddos_protection.max_requests_per_minute}/min")
    else:
        # 如果文件不存在，使用环境变量方式加载
        from core.config import get_config
        config = get_config()
        print(f"[OK] Loaded test config via ENV=test")
except Exception as e:
    print(f"[WARNING] Failed to load test config: {e}")
    print("   Tests will use default config or mocked configs")
