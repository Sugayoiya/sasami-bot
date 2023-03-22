import os
from pathlib import Path

# 资源路径
RESOURCE_PATH = Path() / "resources"
# 图片路径
IMAGE_PATH = RESOURCE_PATH / "image"
# 语音路径
RECORD_PATH = RESOURCE_PATH / "record"
# 文本路径
TEXT_PATH = RESOURCE_PATH / "text"
# 日志路径
LOG_PATH = Path() / "log"
# 字体路径
FONT_PATH = RESOURCE_PATH / "font"
# 数据路径
DATA_PATH = RESOURCE_PATH / "data"
# 临时数据路径
TEMP_PATH = RESOURCE_PATH / "temp"


def load_path():
    old_img_dir = RESOURCE_PATH / "img"
    if not IMAGE_PATH.exists() and old_img_dir.exists():
        os.rename(old_img_dir, IMAGE_PATH)
    old_voice_dir = RESOURCE_PATH / "voice"
    if not RECORD_PATH.exists() and old_voice_dir.exists():
        os.rename(old_voice_dir, RECORD_PATH)
    old_ttf_dir = RESOURCE_PATH / "ttf"
    if not FONT_PATH.exists() and old_ttf_dir.exists():
        os.rename(old_ttf_dir, FONT_PATH)
    old_txt_dir = RESOURCE_PATH / "txt"
    if not TEXT_PATH.exists() and old_txt_dir.exists():
        os.rename(old_txt_dir, TEXT_PATH)
    IMAGE_PATH.mkdir(parents=True, exist_ok=True)
    RECORD_PATH.mkdir(parents=True, exist_ok=True)
    TEXT_PATH.mkdir(parents=True, exist_ok=True)
    LOG_PATH.mkdir(parents=True, exist_ok=True)
    FONT_PATH.mkdir(parents=True, exist_ok=True)
    DATA_PATH.mkdir(parents=True, exist_ok=True)
    TEMP_PATH.mkdir(parents=True, exist_ok=True)


load_path()
