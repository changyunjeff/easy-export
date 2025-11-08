from __future__ import annotations
from pydantic_yaml import parse_yaml_file_as, parse_yaml_raw_as, to_yaml_file
import yaml
import os

from core.schemas import GlobalConfig


def _get_config_file(env: str) -> str|None:
    """
    1. According to the environment variable, get the configuration file path.

    2. If the environment variable is not set, use the default configuration file path.

    3. If the configuration file does not exist, return None.
    """

    config_mapping = {
        "dev": "config.dev.yaml",
        "development": "config.dev.yaml",
        "prod": "config.prod.yaml",
        "production": "config.prod.yaml",
        "test": "config.test.yaml",
        "testing": "config.test.yaml",
    }
    config_path = config_mapping.get(env, "config.dev.yaml")
    # Resolve to absolute path if relative
    config_path = os.path.abspath(config_path)

    # Check file existence
    if os.path.exists(config_path) and os.path.isfile(config_path):
        return config_path
    else:
        return None

def _ensure_open_with_utf8(config_file: str) -> str:
    """
    Ensure the configuration file is opened with UTF-8 encoding.
    """
    with open(config_file, "r", encoding="utf-8") as f:
        return f.read()

def load_config(config_path:str|None = None) -> GlobalConfig:
    """Load configuration from file or environment variables."""
    env = os.getenv("ENV", "dev").lower()
    config_file = config_path
    if config_file is None:
        config_file = _get_config_file(env)
    if config_file is None:
        raise FileNotFoundError(f"Configuration file not found: {config_file}")
    try:
        config_data = _ensure_open_with_utf8(config_file)
    except UnicodeDecodeError:
        raise UnicodeDecodeError(f"Configuration file is not a valid UTF-8 encoded file: {config_file}")
    except yaml.YAMLError:
        raise yaml.YAMLError(f"Configuration file is not a valid YAML file: {config_file}")
    except Exception as e:
        raise Exception(f"Error loading configuration file: {e}")

    try:
        config = parse_yaml_raw_as(GlobalConfig, config_data)
        config.app.mode = env
        return config

    except Exception as e:
        print(f"❌ 预加载配置失败：{str(e)}")
        raise RuntimeError(f"❌ 预加载配置失败：{str(e)}") from e

_global_config = None

def get_config() -> GlobalConfig:
    global _global_config
    if _global_config is None:
        _global_config = load_config()
        print("首次加载全局配置")
    return _global_config
