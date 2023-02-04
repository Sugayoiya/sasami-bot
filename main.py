#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from time import sleep

import nonebot
from nonebot.adapters.onebot.v11 import Adapter

from configs.config import RUNTIME_CONFIG

# # You can pass some keyword args config to init function
# nonebot.init(**RUNTIME_CONFIG)
# app = nonebot.get_asgi()
#
# driver = nonebot.get_driver()
# driver.register_adapter(ONEBOT_V11Adapter)
# # driver.register_adapter(feishuAdapter)
# # driver.register_adapter(TELEGRAMAdapter)
# # driver.register_adapter(kookAdapter)
#
#
# # Please DO NOT modify this file unless you know what you are doing!
# # As an alternative, you should use command `nb` or modify `pyproject.toml` to load plugins
# nonebot.load_plugins("sasami/plugins")
# if InlineGoCQHTTP.enabled:
#     nonebot.load_plugin("nonebot_plugin_gocqhttp")
# sleep(3)
#
# # Modify some config / config depends on loaded configs
# #
# # config = driver.config
# # do something...
#
#
# if __name__ == "__main__":
#     nonebot.logger.warning("Always use `nb run` to start the bot instead of manually running!")
#     nonebot.run(app="__mp_main__:app")


nonebot.init(**RUNTIME_CONFIG)
app = nonebot.get_asgi()

driver = nonebot.get_driver()
driver.register_adapter(Adapter)
config = driver.config

# driver.on_startup(init)
# driver.on_shutdown(disconnect)

# 优先加载定时任务
nonebot.load_plugin("nonebot_plugin_gocqhttp")
sleep(3)
nonebot.load_plugin("nonebot_plugin_apscheduler")
nonebot.load_plugins("plugins")

if __name__ == "__main__":
    nonebot.run(app="__mp_main__:app")