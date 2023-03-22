from pathlib import Path

from pydantic import BaseSettings

from configs.path_config import IMAGE_PATH, TEXT_PATH


class Config(BaseSettings):
    # 中文翻译json文件路径
    cn_zh: Path = TEXT_PATH / "splatoon3" / "CNzh.json"

    # 英文翻译json文件路径
    eu_en: Path = TEXT_PATH / "splatoon3" / "EUen.json"

    # 品牌技能偏向json文件路径
    brand_traits: Path = TEXT_PATH / "splatoon3" / "brandTraits.json"

    # 品牌图片路径
    brand: Path = IMAGE_PATH / "splatoon3" / "brand"

    # 装备技能图片路径
    gear_power: Path = IMAGE_PATH / "splatoon3" / "skill"

    # 装备技能图片路径
    gear: Path = IMAGE_PATH / "splatoon3" / "gear"

    class Config:
        extra = "ignore"
