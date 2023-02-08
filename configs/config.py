import os
from pathlib import Path
from typing import Optional

import yaml

from utils.config_util import ConfigsManager


def load_yml(file: Path, encoding="utf-8") -> dict:
    with open(file, "r", encoding=encoding) as f:
        data = yaml.safe_load(f)
    return data


# 获取当前路径
CONFIG_PATH = Path(os.getcwd()) / "configs" / "config.yml"
config = ConfigsManager(CONFIG_PATH)

RUNTIME_CONFIG = {
    "host": config.get_config("BotSelfConfig", "host"),
    "port": config.get_config("BotSelfConfig", "port"),
    "debug": config.get_config("BotSelfConfig", "debug"),
    "superusers": config.get_config("BotSelfConfig", "superusers"),
    "nickname": config.get_config("BotSelfConfig", "nickname"),
    "command_start": config.get_config("BotSelfConfig", "command_start"),
    "command_sep": config.get_config("BotSelfConfig", "command_sep"),
    "session_expire_timeout": config.get_config("BotSelfConfig", "session_expire_timeout"),
    # "gocq_accounts": config.get_config("InlineGoCQHTTP", "accounts"),
    # "gocq_download_domain": config.get_config("InlineGoCQHTTP", "download_domain"),
    # "gocq_version": config.get_config("InlineGoCQHTTP", "download_version"),
}
print(f"config: {config}")
print(f"RUNTIME_CONFIG: {RUNTIME_CONFIG}")

# 代理，例如 "http://127.0.0.1:7890"
# 如果是WLS 可以 f"http://{hostip}:7890" 使用寄主机的代理
SYSTEM_PROXY: Optional[str] = None  # 全局代理
