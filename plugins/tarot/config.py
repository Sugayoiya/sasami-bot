import json
from pathlib import Path
from typing import Set, Union

import httpx
import nonebot
from aiocache import cached
from pydantic import BaseModel, Extra

from configs.path_config import IMAGE_PATH, TEXT_PATH
from utils.log import logger as log


class PluginConfig(BaseModel, extra=Extra.ignore):
    tarot_path: Path = IMAGE_PATH / "tarot"
    tarot_json: Path = TEXT_PATH / "tarot"
    chain_reply: bool = True
    nickname: Set[str] = {"Bot"}
    if not tarot_path.exists():
        tarot_path.mkdir(parents=True)
    if not tarot_json.exists():
        tarot_json.mkdir(parents=True)


driver = nonebot.get_driver()
tarot_config: PluginConfig = PluginConfig.parse_obj(driver.config.dict())


class DownloadError(Exception):
    pass


class ResourceError(Exception):
    pass


async def download_url(url: str) -> Union[httpx.Response, None]:
    async with httpx.AsyncClient(verify=False) as client:
        for i in range(3):
            try:
                response = await client.get(url)
                if response.status_code != 200:
                    continue
                return response
            except Exception as e:
                log.warning(f"Error occured when downloading {url}, {i + 1}/3: {e}")

    log.warning(f"Abort downloading")
    return None


@driver.on_startup
async def tarot_version_check() -> None:
    '''
        Get the latest version of tarot.json from repo
        If failed, raise exception
    '''
    if not tarot_config.tarot_path.exists():
        tarot_config.tarot_path.mkdir(parents=True, exist_ok=True)

    json_path = tarot_config.tarot_json / "tarot.json"

    url = "https://raw.fastgit.org/MinatoAquaCrews/nonebot_plugin_tarot/master/nonebot_plugin_tarot/tarot.json"
    response = await download_url(url)
    if not json_path.exists():
        if response is None:
            log.warning("Tarot resource missing! Please check!")
            raise ResourceError
    else:
        docs = response.json()
        version = docs.get("version")

        with json_path.open("w", encoding="utf-8") as f:
            json.dump(docs, f, ensure_ascii=False, indent=4)
            log.info(f"Get the latest tarot docs from repo, version: {version}")


@cached(ttl=180)
async def get_tarot(_type: str, _name_cn: str) -> Union[bytes, None]:
    '''
        Downloads tarot image and stores cache temporarily
        if downloading failed, return None
    '''
    log.info(f"Downloading tarot image {_type}/{_name_cn}")

    url = f"https://raw.fastgit.org/MinatoAquaCrews/nonebot_plugin_tarot/master/nonebot_plugin_tarot/resource/BilibiliTarot/{_type}/{_name_cn}"
    data = await download_url(url)
    if data is None:
        log.warning(f"Downloading tarot image {_type}/{_name_cn} failed!")
        return None
    else:
        return data.content
