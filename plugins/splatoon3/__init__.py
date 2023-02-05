from nonebot import get_driver, on_command
from nonebot.adapters.onebot.v11 import MessageSegment, Bot, MessageEvent, GroupMessageEvent
from nonebot.internal.matcher import Matcher

from utils.log import logger as log
from utils.message_builder import custom_forward_msg
from .config import Config
from .core import Splatoon3
from .utils import SplatoonUtils

# 初始化
global_config = get_driver().config
config = Config.parse_obj(global_config)
driver = get_driver()

splatoon3 = Splatoon3()
splatoon3_utils = SplatoonUtils()

salmon_run = on_command('喷3打工', aliases={'喷3打工时间', '喷3打工时间表'}, priority=5, block=True)
regular_battle = on_command('喷3涂地', aliases={'喷3涂地时间', '喷3涂地时间表'}, priority=5, block=True)
ranked_battle = on_command('喷3真格', aliases={'喷3真格时间', '喷3真格时间表'}, priority=5, block=True)

gear_shop = on_command('喷3商店', aliases={'喷3商店时间', '喷3商店时间表'}, priority=5, block=True)


@salmon_run.handle()
async def _(matcher: Matcher):
    log.info(f"推送打工资讯, \n{splatoon3.get_coop_schedules()}")
    await regular_battle.finish(MessageSegment.text("测试打工"))


# 响应回复板块头
@regular_battle.handle()
async def _(matcher: Matcher):
    log.info(f"推送涂地资讯, \n{splatoon3.get_regular_schedules()}")
    await regular_battle.finish(MessageSegment.text("测试涂地"))


@ranked_battle.handle()
async def _(matcher: Matcher):
    log.info(f"推送真格资讯, \n{splatoon3.get_bankara_schedules()}")
    await ranked_battle.finish(MessageSegment.text("测试真格"))


@gear_shop.handle()
async def _(matcher: Matcher, bot: Bot, event: MessageEvent):
    if isinstance(event, GroupMessageEvent):
        pickup_gears, limited_gears = splatoon3.get_gears()

        rst = [MessageSegment.text("特选商品为:")]
        for i in pickup_gears:
            rst.append(MessageSegment.image(splatoon3_utils.img_base64_bytes(i, 'png')))
        rst.append(MessageSegment.text("通常商品为:"))
        for i in limited_gears:
            rst.append(MessageSegment.image(splatoon3_utils.img_base64_bytes(i, 'png')))

        custom_rst = custom_forward_msg(rst, bot.self_id, "鱿鱼须商店")
        await bot.send_group_forward_msg(group_id=event.group_id, messages=custom_rst)
