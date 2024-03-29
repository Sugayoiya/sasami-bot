from nonebot import on_message, get_driver
from nonebot.plugin import PluginMetadata
from nonebot.adapters.onebot.v11.message import MessageSegment
from nonebot.adapters.onebot.v11 import Bot, MessageEvent
from nonebot.exception import ActionFailed, NetworkError
from nonebot.permission import SUPERUSER
from nonebot import require
from nonebot_plugin_apscheduler import scheduler

from pathlib import Path
import hashlib
import random
import re
import string
from utils.log import logger as log
from torch import no_grad, LongTensor
from scipy.io.wavfile import write
import asyncio
import traceback

from .depends import *
from .initial import *
from .config import *
from .utils import *
from .models import SynthesizerTrn
from .function import *
from .text.symbols import symbols_ja, symbols_zh_CHS

__plugin_meta__ = PluginMetadata(
    name="vits角色语音合成本地化",
    description="基于nonebot2和vits的本地化角色语音合成插件",
    usage=f"触发方式：{trigger_rule}[角色名][发送|说][文本内容]\n" +
          "※超级用户管理(若设置前缀，以下均加上前缀)\n" +
          f"   {trigger_rule}[禁用翻译 xxx]   禁用xxx翻译项\n" +
          f"   {trigger_rule}[启用翻译 xxx]   启用xxx翻译项\n" +
          f"   {trigger_rule}[查看翻译]         查看目前可用的翻译项\n" +
          f"   {trigger_rule}[查看禁用翻译]  查看已被禁用的翻译项",
    extra={
        "example": f"{trigger_rule} 宁宁说おはようございます.",
        "author": "dpm12345 <1006975692@qq.com>",
        "version": "0.3.8",
    },
)

symbols_dict = {
    "zh-CHS": symbols_zh_CHS,
    "ja": symbols_ja
}

auto_delete_voice = tts_config.auto_delete_voice
tts_gal = eval(tts_config.tts_character)
tran_type = tts_config.tts_tran_type
prefix = tts_config.tts_prefix
priority = tts_config.tts_priority
driver = get_driver()
__valid_names__ = []
lock_tran_list = {
    "auto": [],
    "manual": []
}


@driver.on_startup
def _():
    log.debug("正在检查目录是否存在...")
    asyncio.ensure_future(check_dir(data_path, base_path, voice_path, model_path, config_path))
    filenames = []
    [filenames.append(model[0])
     for model in tts_gal.values() if not model[0] in filenames]
    log.debug("正在检查配置文件是否存在...")
    asyncio.ensure_future(check_model(model_path, config_path, filenames, tts_gal, __plugin_meta__, __valid_names__))
    log.debug("正在检查配置项...")
    asyncio.ensure_future(check_env(tts_config, tran_type))


voice = on_message(regex(rf"(?:{prefix} *)(?P<name>.+?)(?:说|发送)(?P<text>.+?)$"), block=True, priority=priority)
lock_tran = on_message(regex(rf"(?:{prefix} *)禁用翻译(?: *)(?P<tran>.+)$"), permission=SUPERUSER, block=True,
                       priority=priority)
unlock_tran = on_message(regex(rf"(?:{prefix} *)启用翻译(?: *)(?P<tran>.+)$"), permission=SUPERUSER, block=True,
                         priority=priority)
show_trans = on_message(regex(rf"(?:{prefix} *)查看翻译(?: *)$"), permission=SUPERUSER, block=True, priority=priority)
show_lock_trans = on_message(regex(rf"(?:{prefix} *)查看禁用翻译(?: *)$"), permission=SUPERUSER, block=True,
                             priority=priority)
change_threshold = on_message(regex(rf"(?:{prefix} *)修改阈值(?: *)(?P<threshold>\d+)$"), permission=SUPERUSER,
                              block=True, priority=priority)


async def voice_handler(name: str, text: str):
    log.info(f"tts text：{text}")
    if len(text) > tts_config.tts_token_threshold:
        return text
    # 预处理
    config_file, model_file, index = check_character(name, __valid_names__, tts_gal)
    if config_file == "":
        return "暂时还未有该角色"
    # 生成随机文件名
    first_name = "".join(random.sample([x for x in string.ascii_letters + string.digits], 8))
    filename = hashlib.md5(first_name.encode()).hexdigest() + ".mp3"
    # 加载配置文件
    hps_ms = get_hparams_from_file(config_path / config_file)
    # 翻译的目标语言
    lang = load_language(hps_ms)
    symbols = load_symbols(hps_ms, lang, symbols_dict)
    # 文本处理
    text = changeE2C(text) if lang == "zh-CHS" else changeC2E(text)
    text = await translate(tran_type, lock_tran_list, text, lang)
    if not text:
        return "翻译文本时出错,请查看日志获取细节"
    text = get_text(text, hps_ms, symbols, lang, False)

    try:
        log.debug("加载模型中...")
        net_g_ms = SynthesizerTrn(
            len(symbols),
            hps_ms.data.filter_length // 2 + 1,
            hps_ms.train.segment_size // hps_ms.data.hop_length,
            n_speakers=hps_ms.data.n_speakers,
            **hps_ms.model)
        _ = net_g_ms.eval()
        load_checkpoint(model_path / model_file, net_g_ms)
    except:
        traceback.print_exc()
        return "加载模型失败"

    try:
        log.debug("正在生成中...")
        with no_grad():
            x_tst = text.unsqueeze(0)
            x_tst_lengths = LongTensor([text.size(0)])
            sid = LongTensor([index]) if not index == None else None
            audio = net_g_ms.infer(x_tst, x_tst_lengths, sid=sid, noise_scale=.667,
                                   noise_scale_w=0.8, length_scale=1)[0][0, 0].data.cpu().float().numpy()
        write(voice_path / filename, hps_ms.data.sampling_rate, audio)
        new_voice = Path(change_by_decibel(voice_path / filename, voice_path, tts_config.decibel))
        return new_voice
    except:
        traceback.print_exc()
        return "生成失败"


@voice.handle()
async def _(
        bot: Bot, event: MessageEvent,
        name: str = RegexArg("name"),
        text: str = RegexArg("text")
):
    new_voice = await voice_handler(name, text)
    if isinstance(new_voice, str):
        await voice.finish(MessageSegment.at(event.get_user_id()) + new_voice)
    else:
        try:
            await voice.send(MessageSegment.record(file=new_voice))
        except ActionFailed:
            traceback.print_exc()
            await voice.send("发送失败,请重试")
        except NetworkError:
            traceback.print_exc()
            await voice.send("发送超时,也许等等就好了")
        finally:
            if auto_delete_voice:
                os.remove(new_voice)


@lock_tran.handle()
async def _(tran: str = RegexArg("tran")):
    if tran == "youdao":
        await lock_tran.send(f"该翻译项禁止禁用!")
    elif tran in tran_type:
        if tran not in lock_tran_list["manual"]:
            lock_tran_list["manual"].append(tran)
        log.info(f"禁用成功")
        await lock_tran.send(f"禁用成功")
    else:
        await lock_tran.send(f"未有{tran}翻译项")


@unlock_tran.handle()
async def _(tran: str = RegexArg("tran")):
    if tran in lock_tran_list["auto"] or tran in lock_tran_list["manual"]:
        if tran in lock_tran_list["auto"]:
            lock_tran_list["auto"].remove(tran)
        if tran in lock_tran_list["manual"]:
            lock_tran_list["manual"].remove(tran)
        log.info(f"启用成功")
        await lock_tran.send(f"启用成功")
    else:
        await lock_tran.send(f"{tran}翻译项未被禁用")


@show_trans.handle()
async def _():
    present_trans = [tran for tran in tran_type if tran not in lock_tran_list["auto"]
                     and tran not in lock_tran_list["manual"]]
    await show_trans.send(f"目前支持的翻译:{','.join(present_trans)}")


@show_lock_trans.handle()
async def _():
    lock_list = lock_tran_list["auto"].copy()
    for tran in lock_tran_list["manual"]:
        if tran not in lock_list:
            lock_list.append(tran)
    if len(lock_list) == 0:
        await show_lock_trans.send("目前没有翻译项被禁用")
    else:
        await show_lock_trans.send(f"目前被禁用项{','.join(lock_list)}")


@change_threshold.handle()
async def _(threshold: str = RegexArg("threshold")):
    if threshold.isdigit():
        threshold = int(threshold)
        if threshold < 0 or threshold > 100:
            await change_threshold.send("阈值必须在0-100之间")
        else:
            tts_config.tts_token_threshold = threshold
            await change_threshold.send(f"阈值已修改为{threshold}")
    else:
        await change_threshold.send("阈值必须是数字")


# 每月重置自动禁用的翻译项
@scheduler.scheduled_job("cron", day=1, minute=5, misfire_grace_time=60)
async def reset_tran():
    lock_tran_list["auto"].clear()
    valid_tran_type = [tran for tran in tran_type if tran not in lock_tran_list["manual"]]
    log.info(f"目前可用翻译:{','.join(valid_tran_type)}")
