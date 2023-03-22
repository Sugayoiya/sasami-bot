from nonebot import on_command
from nonebot.adapters.onebot.v11 import GROUP_ADMIN, GROUP_OWNER, GroupMessageEvent
from nonebot.permission import SUPERUSER
from nonebot_plugin_apscheduler import scheduler

from utils.log import logger as log
from .data_source import drink_manager

__drink_reminder__ = "v0.0.1"
__drink_reminder__ = f'''
群喝水提醒小助手？ {__drink_reminder__}
[开启喝水小助手]    开启群喝水小助手
[关闭喝水小助手]    关闭群喝水小助手'''.strip()

drink_reminder_on = on_command("开启喝水小助手", permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER,
                               priority=12,
                               block=True)
drink_reminder_off = on_command("关闭喝水小助手", permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER,
                                priority=12,
                                block=True)


@drink_reminder_on.handle()
async def _(event: GroupMessageEvent):
    gid = str(event.group_id)
    drink_manager.update_groups_on(gid, True)
    await drink_reminder_on.finish("已开启提醒喝水小助手~")


@drink_reminder_off.handle()
async def _(event: GroupMessageEvent):
    gid = str(event.group_id)
    drink_manager.update_groups_on(gid, False)
    await drink_reminder_off.finish("已关闭提醒喝水小助手~")


# 喝水提醒
@scheduler.scheduled_job("cron", hour="8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23", minute=0, misfire_grace_time=60)
async def drink_reminder_scheduler():
    await drink_manager.drink_reminder()
    log.debug("喝水提醒任务执行完毕")

# @scheduler.scheduled_job("cron", hour="23", minute=9, misfire_grace_time=60)
# async def drink_reminder_scheduler():
#     await drink_manager.drink_reminder()
#     log.debug("喝水提醒任务执行完毕")
