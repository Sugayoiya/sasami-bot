import random
from pathlib import Path
from typing import Union, Dict, List

from nonebot import get_bot
from nonebot.adapters.onebot.v11 import ActionFailed

from configs.path_config import TEXT_PATH
from utils.json_util import load_json, save_json
from utils.log import logger as log

drink_list = ["俗话说\"女人是水造的\"，所以身为女生就要时刻喝水，这样就可以保持充足的水分，皮肤、头发就会更有光泽~",
              "喝多点水还可以保持身材哦，因为水促进了我们身体的循环~",
              "该喝水了哟，喝多点水整体上也会容光焕发~",
              "该喝水了哟，要多爱护自己，多喝水、多吃新鲜水果蔬菜、尽量保证充足睡眠。加油！",
              "多喝水很简单的话，多喝水对身体好！只有心中挂念着你们的人才会说你的家人也老说的话：你要多喝水呀！！~",
              "天气寒冷干燥。多喝水，注意保暖。少抽烟喝酒吃辣。多想念我~"
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

    def update_groups_on(self, gid: str, new_state: bool) -> None:
        '''
            Turn on/off greeting tips in group
        '''
        self._drink_reminder = load_json(self._drink_reminder_group_json)

        if new_state:
            if gid not in self._drink_reminder["groups_id"]:
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
                except ActionFailed as e:
                    log.warning(f"发送群 {gid} 失败：{e}")


drink_manager = DrinkManager()

__all__ = [
    drink_manager
]
