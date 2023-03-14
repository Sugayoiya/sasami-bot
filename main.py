#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from time import sleep

import nonebot
from nonebot.adapters.onebot.v11 import Adapter

from configs.config import RUNTIME_CONFIG

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
