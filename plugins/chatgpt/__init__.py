from nonebot.adapters.onebot.v11 import MessageEvent
from nonebot.adapters.onebot.v11.bot import Bot
from nonebot.plugin import on_message
from nonebot.rule import to_me

from configs.path_config import TEXT_PATH
from utils.utils import cooldow_checker
from .chatGPT import Chatbot

__plugin_name__ = "chatgpt"

__plugin_usage__ = """
usage：
    chatgpt
""".strip()

path = TEXT_PATH / "chatgpt" / "config.json"
chatgpt = on_message(priority=98, block=False, rule=to_me())
chat_bot = Chatbot("")
chat_bot.load_config(path)


@chatgpt.handle()
async def _(bot: Bot, event: MessageEvent):
    # 不响应自身发送的消息
    if event.sender.user_id == event.self_id:
        return
    res = chat_bot.ask_stream(event.get_plaintext())
    await chatgpt.finish(res)
