from nonebot import on_command
from nonebot.adapters.onebot.v11 import GROUP_ADMIN, GROUP_OWNER, GroupMessageEvent
from nonebot.permission import SUPERUSER
from nonebot_plugin_apscheduler import scheduler

from .data_source import drink_manager

__what2eat_version__ = "v0.3.4"
__what2eat_notes__ = f'''
今天吃什么？ {__what2eat_version__}
[xx吃xx]    问bot吃什么
[xx喝xx]    问bot喝什么
[添加 xx]   添加菜品至群菜单
[移除 xx]   从菜单移除菜品
[加菜 xx]   添加菜品至基础菜单
[菜单]        查看群菜单
[开启/关闭小助手] 开启/关闭吃饭小助手
[添加/删除问候 时段 问候语] 添加/删除吃饭小助手问候语'''.strip()

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
