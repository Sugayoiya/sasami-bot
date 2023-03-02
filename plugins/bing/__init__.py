from nonebot.adapters.onebot.v11 import MessageEvent
from nonebot.adapters.onebot.v11.bot import Bot
from nonebot.plugin import on_message, on_command
from nonebot.rule import to_me

from utils.utils import cooldow_checker
from .bing import Bing

__plugin_name__ = "bing"

__plugin_usage__ = """
usage：
    bing
""".strip()

bing = on_message(priority=98, block=False, rule=to_me())
chat_bot = Bing()


@bing.handle(parameterless=[cooldow_checker("bing", 20)])
async def _(bot: Bot, event: MessageEvent):
    # 不响应自身发送的消息
    if event.sender.user_id == event.self_id:
        return
    res = await chat_bot.ask_stream(event.get_plaintext())
    await bing.finish(res)


bing_reset = on_command("重置会话", aliases={"bing重置会话"}, priority=97, block=True)


@bing_reset.handle(parameterless=[cooldow_checker("bing重置会话", 10)])
async def _(bot: Bot, event: MessageEvent):
    await chat_bot.reset()
    await bing_reset.finish("重置成功")
