from nonebot import on_regex, require
from nonebot.adapters.onebot.v11 import MessageEvent
from nonebot.adapters.onebot.v11.helpers import Cooldown
from nonebot.params import RegexMatched

from .worldcup import WorldCup

require("nonebot_plugin_apscheduler")

__world_cup_notes__ = f'''
世界杯小助手(暂时功能/已过时)
[世界杯帮助] 返回世界杯小助手帮助
[世界杯源/直播/直播源] 返回抖音/咪咕视频世界杯直播源
[世界杯赛程] 返回当天世界杯赛程
'''.strip()

world_cup = on_regex(r"^世界杯(帮助)?$", priority=15)
world_cup_source = on_regex(r"^世界杯(源|直播|直播源)$", priority=15)
world_cup_schedule = on_regex(r"^世界杯赛程(今天|明天|本周|下周)?$", priority=15)
world_cup_helper = WorldCup()


@world_cup.handle()
async def _(event: MessageEvent, args: str = RegexMatched()):
    await world_cup.finish(__world_cup_notes__)


@world_cup_source.handle([Cooldown(60)])
async def _(event: MessageEvent, args: str = RegexMatched()):
    msg = world_cup_helper.echo()
    await world_cup.finish(msg)


@world_cup_schedule.handle()
async def _(event: MessageEvent, args: str = RegexMatched()):
    msg = world_cup_helper.schedule(args)
    await world_cup_schedule.finish(msg)
