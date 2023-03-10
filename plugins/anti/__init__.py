# """
# @Author         : Ailitonia
# @Date           : 2022/04/28 20:26
# @FileName       : omega_anti_flash.py
# @Project        : nonebot2_miya
# @Description    : Omega 反闪照插件
# @GitHub         : https://github.com/Ailitonia
# @Software       : PyCharm
# """
#
# from typing import Union
#
# from nonebot.adapters.onebot.v11.bot import Bot
# from nonebot.adapters.onebot.v11.event import GroupMessageEvent, GroupRecallNoticeEvent
# from nonebot.adapters.onebot.v11.message import Message, MessageSegment
# from nonebot.adapters.onebot.v11.permission import GROUP
# from nonebot.plugin import on_message, PluginMetadata, on_notice
#
# from utils.log import logger as log
#
# __plugin_meta__ = PluginMetadata(
#     name="反闪照",
#     description="【AntiFlash 反闪照插件】\n"
#                 "检测闪照并提取原图",
#     usage="仅限群聊中群管理员使用:\n"
#           "/AntiFlash <ON|OFF>",
#     extra={"author": "Ailitonia"},
# )
#
# from utils.utils import MessageChecker
#
# AntiFlash = on_message(
#     permission=GROUP,
#     priority=100,
#     block=False
# )
#
#
# @AntiFlash.handle()
# async def check_flash_img(bot: Bot, event: GroupMessageEvent):
#     # 不响应自身发送的消息
#     if event.sender.user_id == event.self_id:
#         return
#
#     for msg_seg in event.message:
#         if msg_seg.type == 'image':
#             if msg_seg.data.get('type') == 'flash':
#                 if msg_seg.data.get('url', None):
#                     img_file = msg_seg.data.get('url')
#                 else:
#                     img_file = msg_seg.data.get('file')
#                 img_seq = MessageSegment.image(file=img_file)
#                 log.debug(f'AntiFlash 反闪照已捕获并处理闪照, 闪照文件: {img_file}')
#                 for user_id in bot.config.superusers:
#                     await bot.send_private_msg(user_id=int(user_id), message='已检测到闪照:\n' + img_seq)
#
#
# AntiRecall = on_notice(
#     priority=99,
#     block=False
# )
#
#
# @AntiRecall.handle()
# async def check_recall_notice(bot: Bot, event: GroupRecallNoticeEvent):
#     user_id = event.user_id
#     # 不响应自己撤回或由自己撤回的消息
#     if user_id == event.self_id or event.operator_id == event.self_id:
#         return
#     message = await bot.get_msg(message_id=event.message_id)
#     user = event.user_id
#     group = event.group_id
#     message = message["message"]
#     try:
#         m = recall_msg_dealer(message)
#     except Exception:
#         check = MessageChecker(message).check_cq_code
#         if not check:
#             m = message
#         else:
#             return
#     msg = f"主人，咱拿到了一条撤回信息！\n{user}@[群:{group}]\n撤回了\n{m}"
#     for user_id in bot.config.superusers:
#         await bot.send_private_msg(user_id=int(user_id), message=Message(msg))
#
#
# def recall_msg_dealer(msg: Union[str, dict]) -> str:
#     if isinstance(msg, str):
#         return msg
#     temp_m = list()
#     for i in msg:
#         _type = i.get("type", "idk")
#         _data = i.get("data", "idk")
#         if _type == "text":
#             temp_m.append(_data["text"])
#         elif _type == "image":
#             url = _data["url"]
#             check = MessageChecker(url).check_image_url
#             if check:
#                 temp_m.append(MessageSegment.image(url))
#             else:
#                 temp_m.append(f"[该图片可能包含非法内容，源url：{url}]")
#         elif _type == "face":
#             temp_m.append(MessageSegment.face(_data["id"]))
#         else:
#             temp_m.append(f"[未知类型信息：{_data}]")
#
#     repo = str().join(map(str, temp_m))
#     return repo
