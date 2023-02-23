from nonebot.adapters.onebot.v11 import MessageEvent
from nonebot.adapters.onebot.v11.bot import Bot
from nonebot.plugin import on_message
from nonebot.rule import to_me

from utils.utils import cooldow_checker
from .chatGPT_v1 import ChatGPT

__plugin_name__ = "chatgpt"

__plugin_usage__ = """
usage：
    chatgpt
""".strip()

chatgpt = on_message(priority=98, block=False, rule=to_me())
chat_bot = ChatGPT()


@chatgpt.handle(parameterless=[cooldow_checker("chatgpt", 30)])
async def _(bot: Bot, event: MessageEvent):
    # 不响应自身发送的消息
    if event.sender.user_id == event.self_id:
        return
    res = await chat_bot.ask(event.get_plaintext())
    await chatgpt.finish(res)
