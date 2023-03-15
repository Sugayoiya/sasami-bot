from pydantic import Extra, BaseModel
from nonebot import get_driver
from typing import List

from configs.path_config import DATA_PATH

data_path = DATA_PATH
base_path = data_path / "tts"
voice_path = base_path / "voice"
model_path = base_path / "model"
config_path = base_path / "config"
emotion_path = base_path / "emotion"
embedding_path = base_path / "embedding"
hubert_path = base_path / "hubert"
jieba_path = base_path / "jieba"


class Config(BaseModel, extra=Extra.ignore):
    tts_character: str = '{():[""]}'
    auto_delete_voice: bool = False
    decibel: int = -10
    tts_at: bool = True
    tts_prefix: str = ""
    tts_priority: int = 3
    tts_tran_type: List[str] = ["youdao"]
    # nas配置不够, 40个字符为限, 上了pc 2070s 直接拉满
    tts_token_threshold: int = 9999
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
