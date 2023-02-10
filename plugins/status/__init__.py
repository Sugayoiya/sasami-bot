from nonebot import get_bot
from nonebot.plugin import on_command
from nonebot_plugin_apscheduler import scheduler

from configs.config import config
from utils.log import logger as log
from .data_source import Status

ping = on_command("ping")


@ping.handle()
async def _():
    await ping.finish(Status.ping())


status = on_command("status")


@status.handle()
async def _():
    msg, _ = Status.get_status()
    await status.finish(msg)


info_msg = "アトリは高性能ですから！"


@scheduler.scheduled_job("interval", name="状态检查", minutes=10, misfire_grace_time=15,
                         id="status_check")  # type: ignore
async def _():
    log.debug("开始检查资源消耗...")
    msg, stat = Status().get_status()
    if not stat:
        log.warning(msg)

        bot = get_bot()
        for superuser in config.get_config("BotSelfConfig", "superusers"):
            await bot.send_private_msg(user_id=superuser, message=msg)

    log.debug("资源消耗正常")
