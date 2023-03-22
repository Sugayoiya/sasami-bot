from pydantic import Extra, BaseModel
from nonebot import get_driver
from typing import List

from configs.path_config import DATA_PATH

data_path = DATA_PATH
base_path = data_path / "tts"
voice_path = base_path / "voice"
model_path = base_path / "model"
config_path = base_path / "config"


class Config(BaseModel, extra=Extra.ignore):
    tts_character: str = '{():[""]}'
    auto_delete_voice: bool = True
    decibel: int = -10
    tts_at: bool = True
    tts_prefix: str = ""
    tts_priority: int = 3
    tts_tran_type: List[str] = ["youdao"]
    # nas配置不够, 40个字符为限
    tts_token_threshold: int = 40
    baidu_tran_appid: str = ""
    baidu_tran_apikey: str = ""
    tencent_tran_region: str = "ap-shanghai"
    tencent_tran_secretid: str = ""
    tencent_tran_secretkey: str = ""
    tencent_tran_projectid: int = 0


tts_config = Config.parse_obj(get_driver().config)
trigger_rule = ""
if tts_config.tts_at:
    trigger_rule += "@机器人 "
trigger_rule += tts_config.tts_prefix
