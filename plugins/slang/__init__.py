from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, Event, Message
from nonebot.log import logger
from nonebot.params import CommandArg, ArgStr
from nonebot.typing import T_State

from .data import text_to_emoji

slang = on_command("abstract", aliases={"抽象话", "抽象化"}, priority=5, block=True)


@slang.handle()
async def _(state: T_State = T_State, arg: Message = CommandArg()):
    if arg.extract_plain_text().strip():
        state["abstract"] = arg.extract_plain_text().strip()


@slang.got("abstract", prompt="你要发什么推？")
async def _(bot: Bot, event: Event, target_text: str = ArgStr("abstract")):
    abstract_responses = text_to_emoji(target_text)
    if abstract_responses:
        logger.info("抽象成功！")
        await slang.send(abstract_responses)
    else:
        logger.error("抽象失败~")
        await slang.send("抽象异常了~一定是程序出了点问题！")
