from typing import Tuple, Any

from nonebot import on_regex
from nonebot.adapters.onebot.v11 import MessageEvent, PRIVATE
from nonebot.params import RegexGroup

from utils import withdraw_message_manager
from utils.log import logger as log
from utils.message_builder import image

# from configs.config import Config

__plugin_name__ = "coser"
__plugin_usage__ = """
usage：
    指令：
        ?N连cos/coser
        示例：cos
        示例：5连cos （单次请求张数小于9）
""".strip()
__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": ["cos", "coser", "括丝", "COS", "Cos", "cOS", "coS"],
}
__plugin_configs__ = {
    "WITHDRAW_COS_MESSAGE": {
        "value": (0, 1),
        "help": "自动撤回，参1：延迟撤回色图时间(秒)，0 为关闭 | 参2：监控聊天类型，0(私聊) 1(群聊) 2(群聊+私聊)",
        "default_value": (0, 1),
    },
}

coser = on_regex(r"^(\d)?连?(cos|COS|coser|括丝)$", priority=5, block=True, permission=PRIVATE)

# 纯cos，较慢:https://picture.yinux.workers.dev
# 比较杂，有福利姬，较快:https://api.jrsgslb.cn/cos/url.php?return=img
url = "https://api.jrsgslb.cn/cos/url.php?return=img"

withdraw = withdraw_message_manager.WithdrawMessageManager()


@coser.handle()
async def _(event: MessageEvent, reg_group: Tuple[Any, ...] = RegexGroup()):
    num = reg_group[0] or 1
    for _ in range(int(num)):
        try:
            msg_id = await coser.send(image(url))
            withdraw.withdraw_message(
                event,
                msg_id["message_id"],
                (0, 1),
            )
        except Exception as e:
            await coser.send("你cos给我看！")
            log.error(f"cos 发送了未知错误 {type(e)}：{e}")