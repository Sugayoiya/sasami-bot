from typing import Tuple, Any
import os
import traceback
from typing import Tuple, Any

from nonebot import get_bot
from nonebot import on_command, on_regex
from nonebot.adapters.onebot.v11 import (
    ActionFailed,
    NetworkError,
    Bot,
    Event,
    Message,
    MessageSegment,
)
from nonebot.adapters.onebot.v11.helpers import extract_image_urls
from nonebot.params import CommandArg, RegexGroup, ArgStr
from nonebot.permission import SUPERUSER
from nonebot.rule import to_me
from nonebot.typing import T_State

from utils.log import logger as log
from ..tts import voice_handler
from ..tts.config import tts_config
from ..tts.function import character_list

cmd_voice = "语音"
cmd_image = "图片"
cmd_text = "文字"

type_group = "群"
type_private = "私"

tts_character = eval(tts_config.tts_character)
DEFAULT_CHARACTER = "路易丝"
character_name = DEFAULT_CHARACTER

send = on_regex(rf"^发({cmd_voice}|{cmd_image}|{cmd_text})+到({type_group}|{type_private})+(\d+)[\s]+(.*)",
                priority=15, permission=SUPERUSER, block=True, rule=to_me())


@send.handle()
async def _(bot: Bot, event: Event, reg_group: Tuple[Any, ...] = RegexGroup()):
    cmd = reg_group[0].strip()
    message_type = reg_group[1].strip()
    target = reg_group[2].strip()
    message = reg_group[3].strip()
    log.debug(f"cmd: {cmd}, type: {message_type}, target: {target}")
    bot = get_bot()
    if cmd == cmd_voice:
        new_voice = await voice_handler(character_name, message)
        try:
            await bot.call_api("send_group_msg", group_id=target, message=MessageSegment.record(new_voice)) \
                if message_type == type_group else await bot.call_api("send_private_msg", user_id=target,
                                                                      message=MessageSegment.record(new_voice))
        except (ActionFailed, NetworkError):
            traceback.print_exc()
        finally:
            os.remove(new_voice)
    elif cmd == cmd_image:
        img = extract_image_urls(event.get_message())
        if not img:
            return
        await bot.call_api("send_group_msg", group_id=target, message=MessageSegment.image(img[0])) \
            if message_type == type_group else await bot.call_api("send_private_msg", user_id=target,
                                                                  message=MessageSegment.image(img[0]))
    elif cmd == cmd_text:
        await bot.call_api("send_group_msg", group_id=target, message=message) \
            if message_type == type_group else await bot.call_api("send_private_msg", user_id=target, message=message)


sender_config = on_command("sender", permission=SUPERUSER, priority=15, block=True, rule=to_me())


@sender_config.handle()
async def _(state: T_State = T_State, arg: Message = CommandArg()):
    if arg.extract_plain_text().strip():
        state["chatgpt"] = arg.extract_plain_text().strip()


@sender_config.got("chatgpt", prompt="目前支持的角色有:" + str(character_list(tts_character)))
async def _(bot: Bot, target_text: str = ArgStr("chatgpt")):
    global character_name
    if target_text in character_list(tts_character):
        character_name = target_text
        await sender_config.finish("语音配置成功！")
    else:
        await sender_config.finish("角色不存在，使用默认配置: " + DEFAULT_CHARACTER)
