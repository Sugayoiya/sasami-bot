import datetime
import os
import traceback

from nonebot.adapters.onebot.v11 import MessageEvent, Message
from nonebot.adapters.onebot.v11.bot import Bot
from nonebot.adapters.onebot.v11.message import MessageSegment
from nonebot.exception import ActionFailed, NetworkError
from nonebot.params import CommandArg, ArgStr
from nonebot.permission import SUPERUSER
from nonebot.plugin import on_message, on_command
from nonebot.rule import to_me
from nonebot.typing import T_State

from configs.path_config import TEXT_PATH
from utils.utils import cooldown_checker
from .chatGPT import Chatbot
from ..tts import voice_for_chatgpt
from ..tts.config import tts_gal_config
from ..tts.function import character_list

__plugin_name__ = "chatgpt"
__plugin_cooldown__ = 30
__plugin_usage__ = """
usage：
    chatgpt
""".strip()

path = TEXT_PATH / "chatgpt" / "config.json"
tts_gal = eval(tts_gal_config.tts_gal)

chat_bot = Chatbot("")
chat_bot.load_config(path)

DEFAULT_CHARACTER = "路易丝"
character_name = DEFAULT_CHARACTER

# 获取最后一次调用chatgpt的时间，默认为加载插件时间
last_time = datetime.datetime.now()

chatgpt = on_message(priority=98, block=False, rule=to_me())

chatgpt_config = on_command("chatgpt_config", aliases={"语音配置", "cv"}, permission=SUPERUSER,
                            priority=15, block=True, rule=to_me())


@chatgpt_config.handle()
async def _(state: T_State = T_State, arg: Message = CommandArg()):
    if arg.extract_plain_text().strip():
        state["chatgpt"] = arg.extract_plain_text().strip()


@chatgpt_config.got("chatgpt", prompt="目前支持的角色有:" + str(character_list(tts_gal)))
async def _(bot: Bot, target_text: str = ArgStr("chatgpt")):
    global character_name
    if target_text in character_list(tts_gal):
        character_name = target_text
        await chatgpt_config.finish("语音配置成功！")
    else:
        await chatgpt_config.finish("角色不存在，使用默认配置: " + DEFAULT_CHARACTER)


@chatgpt.handle(parameterless=[cooldown_checker(__plugin_name__, __plugin_cooldown__)])
async def _(bot: Bot, event: MessageEvent):
    # 当前时间比上次调用时间间隔小于30秒，人为设置cd
    global last_time
    if (datetime.datetime.now() - last_time).seconds < __plugin_cooldown__:
        return
    last_time = datetime.datetime.now()
    # 不响应自身发送的消息
    if event.sender.user_id == event.self_id:
        return
    res = chat_bot.ask_stream(event.get_plaintext())
    new_voice = await voice_for_chatgpt(character_name, "".join(res))
    if isinstance(new_voice, str):
        await chatgpt.finish(new_voice)
    else:
        try:
            await chatgpt.send(MessageSegment.record(file=new_voice))
        except (ActionFailed, NetworkError):
            traceback.print_exc()
            await chatgpt.finish(new_voice)
        finally:
            os.remove(new_voice)
