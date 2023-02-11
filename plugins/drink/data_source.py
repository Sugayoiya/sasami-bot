import random
from pathlib import Path
from typing import Union, Dict, List

from nonebot import get_bot
from nonebot.adapters.onebot.v11 import ActionFailed

from configs.path_config import TEXT_PATH
from utils.json_util import load_json, save_json
from utils.log import logger as log

# from chatGPT
drink_list: List[str] = [
    "喝水的好时机到啦！💦 把每一口水都变成对身体的呵护！👍",
    "每天都要保持健康！💪 喝水是最简单的方法之一！💦",
    "把喝水当成一件小乐事吧！😊 它能帮助你保持更棒的身体状态！💪",
    "水是生命之源！💧 没有它，生命就会变得干涸！💔 快快喝一口吧！",
    "现在是喝水的好时机！🕰️ 把每一口水都变成对身体的呵护！👍",
    "喝水不仅能帮助你保持健康，还能帮助你保持清醒！💡 把它当成一种习惯！",
    "一天之中，有多少时间是专门留给喝水的呢？🤔 让我们一起把每一天都变得更美好！🌞",
    "每一口水都是对身体的关爱！❤️ 喝水是一件很重要的事情，不要忘记！💧",
    "喝水时间到了！🚨 让我们一起为身体加油！💪",
    "水不仅让你保持清新，还能让你保持快乐！💦 让我们一起享受喝水的乐趣！😊",
    "喝水不仅对身体有益，也对心情有益！💧 让我们一起让自己感觉更好！👍",
    "每天都要保持健康！💪 喝水是最简单的方法之一！💦",
    "让我们一起为身体充充电！🔋 喝水是最好的选择！💧",
    "喝水可以让你保持清醒，保持活力！💪 快快喝一口水吧！💦",
    "每一口水都是对身体的关爱！❤️ 让我们一起为自己喝水吧！💧",
    "保持健康不仅需要运动，也需要喝水！💦 让我们一起为身体加油！💪",
    "水是生命之源，让我们一起为身体补充元素！💦💪",
    "保持身体水分平衡是健康的关键！💦 让我们一起爱护自己！❤️",
    "一天之中最简单的健康小习惯：喝水！💧 让我们一起保持健康！💪",
    "水是活力的源泉，让我们一起为身体充充电！💦🔋",
    "喝水不仅对身体有益，还能改善皮肤！💦❤️ 让我们一起爱护自己！",
    "每一口水都是对身体的呵护！💧 让我们一起保持健康！❤️",
    "水不仅能够让你保持清醒，还能让你保持积极！💦💪 让我们一起喝水吧！",
    "保持身体水分平衡是保持健康的关键！💦❤️ 让我们一起爱护自己！"
]


class DrinkManager:
    def __init__(self):
        self._quote: list[str] = []
        self._drink_reminder: Dict[str, Union[List[str], Dict[str, bool]]] = {}
        self._drink_path: Path = TEXT_PATH / "drink"
        self._drink_reminder_group_json: Path = self._drink_path / "drink_reminder_group.json"

        if not self._drink_path.exists():
            self._drink_path.mkdir(parents=True)
        if not self._drink_reminder_group_json.exists():
            save_json(self._drink_reminder_group_json, {"groups_id": {}})
        self._drink_reminder = load_json(self._drink_reminder_group_json)

    def update_groups_on(self, gid: str, new_state: bool) -> None:
        '''
            Turn on/off greeting tips in group
        '''
        self._drink_reminder = load_json(self._drink_reminder_group_json)

        if new_state:
            self._drink_reminder["groups_id"].update({gid: True})
        else:
            if gid in self._drink_reminder["groups_id"]:
                self._drink_reminder["groups_id"].update({gid: False})

        save_json(self._drink_reminder_group_json, self._drink_reminder)

    async def drink_reminder(self):
        '''
            获取百分比菜单
        '''
        bot = get_bot()
        for gid in self._drink_reminder["groups_id"]:
            if self._drink_reminder["groups_id"].get(gid, False):
                try:
                    await bot.call_api("send_group_msg", group_id=int(gid), message=random.choice(drink_list))
                    log.info(f"群 {gid} 发送提醒喝水成功")
                except ActionFailed as e:
                    log.warning(f"群 {gid} 发送提醒喝水失败：{e}")


drink_manager = DrinkManager()

__all__ = [
    drink_manager
]
