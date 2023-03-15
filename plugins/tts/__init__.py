import asyncio
import os
import string
import traceback
import librosa
from pathlib import Path

from nonebot import on_message
from nonebot.exception import ActionFailed, NetworkError
from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata
from nonebot_plugin_apscheduler import scheduler
from scipy.io.wavfile import write

from .mel_processing import spectrogram_torch
from .config import *
from .depends import *
from .function import *
from .initial import *
from .models import SynthesizerTrn
from .text.symbols import symbols_ja, symbols_zh_CHS
from .utils import *

__plugin_meta__ = PluginMetadata(
    name="vits_tts",
    description="base on nonebot2 and vits_tts",
    usage=f"触发方式：{trigger_rule}[角色名][发送|说][文本内容]\n" +
          "※超级用户管理(若设置前缀，以下均加上前缀)\n" +
          f"   {trigger_rule}[禁用翻译 xxx]   禁用xxx翻译项\n" +
          f"   {trigger_rule}[启用翻译 xxx]   启用xxx翻译项\n" +
          f"   {trigger_rule}[查看翻译]       查看目前可用的翻译项\n" +
          f"   {trigger_rule}[查看禁用翻译]    查看已被禁用的翻译项\n" +
          f"   {trigger_rule}[修改阈值 数字]   修改生成语音的文字长度阈值\n",
    extra={
        "example": f"{trigger_rule} 宁宁说おはようございます.",
        "author": "moko",
        "version": "0.0.1",
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
    asyncio.ensure_future(
        check_dir(data_path, base_path, voice_path, model_path, config_path,
                  emotion_path, embedding_path, hubert_path, jieba_path))
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

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


async def voice_handler(name: str, text: str):
    log.info(f"tts text：{text}")
    if len(text) > tts_config.tts_token_threshold:
        return text
    # preprocess
    config_file, model_file, index = check_character(name, __valid_names__, tts_gal)
    # replace &#91; &#93; to [ ] for qq message
    text = check_text(text)
    if config_file == "":
        return "no character"
    # generate random filename
    first_name = "".join(random.sample([x for x in string.ascii_letters + string.digits], 8))
    filename = hashlib.md5(first_name.encode()).hexdigest() + ".mp3"
    # loading model config
    hps_ms = get_hparams_from_file(config_path / config_file)
    n_speakers = hps_ms.data.n_speakers if 'n_speakers' in hps_ms.data.keys() else 0
    n_symbols = len(hps_ms.symbols) if 'symbols' in hps_ms.keys() else 0
    # use_f0 = hps_ms.data.use_f0 if 'use_f0' in hps_ms.data.keys() else False
    # symbols = load_symbols(hps_ms, symbols_dict)
    emotion_embedding = hps_ms.data.emotion_embedding if 'emotion_embedding' in hps_ms.data.keys() else False

    # 文本处理 也许不再需要普通的翻译了
    # text = changeE2C(text) if lang == "zh-CHS" else changeC2E(text)
    # text = await translate(tran_type, lock_tran_list, text, lang)
    # if not text:
    #     return "翻译文本时出错,请查看日志获取细节"

    try:
        log.debug("loading model...")
        net_g_ms = SynthesizerTrn(
            n_symbols,
            hps_ms.data.filter_length // 2 + 1,
            hps_ms.train.segment_size // hps_ms.data.hop_length,
            n_speakers=n_speakers,
            emotion_embedding=emotion_embedding,
            **hps_ms.model).to(device)
        _ = net_g_ms.eval()
        load_checkpoint(model_path / model_file, net_g_ms)
    except:
        traceback.print_exc()
        return "fail to load model"

    if n_symbols > 0:
        length_scale, text = get_label_value(text, 'LENGTH', 1, 'length scale')
        noise_scale, text = get_label_value(text, 'NOISE', 0.667, 'noise scale')
        noise_scale_w, text = get_label_value(text, 'NOISEW', 0.8, 'deviation of noise')
        cleaned, text = get_label(text, 'CLEANED')
        text = get_text(text, hps_ms, cleaned)

        if not emotion_embedding:
            try:
                log.debug("generating voice without embedding...")
                with no_grad():
                    x_tst = text.unsqueeze(0).to(device)
                    x_tst_lengths = LongTensor([text.size(0)]).to(device)
                    sid = LongTensor([index]).to(device) if index is not None else None
                    audio = net_g_ms.infer(x_tst, x_tst_lengths, sid=sid, noise_scale=noise_scale,
                                           noise_scale_w=noise_scale_w, length_scale=length_scale)[0][0, 0] \
                        .data.to(device).cpu().float().numpy()
                write(voice_path / filename, hps_ms.data.sampling_rate, audio)
                new_voice = Path(change_by_decibel(voice_path / filename, voice_path, tts_config.decibel))
                return new_voice
            except:
                traceback.print_exc()
                return "fail to generate voice"
            finally:
                torch.cuda.empty_cache()
        else:
            import numpy as np
            import audonnx

            w2v2_model = audonnx.load(emotion_path)
            embedding_refer = os.listdir(embedding_path)[0]
            # emotion_file = emotion_path / w2v2_refer
            embedding_file = embedding_path / embedding_refer

            if embedding_refer.endswith('.npy'):
                emotion = np.load(embedding_file)
                emotion = FloatTensor(emotion).unsqueeze(0)
            else:
                audio16000, sampling_rate = librosa.load(os.path.abspath(embedding_file), sr=16000, mono=True)
                emotion = w2v2_model(audio16000, sampling_rate)['hidden_states']
                embedding_file = re.sub(r'\..*$', '', os.path.abspath(embedding_file))
                np.save(embedding_file, emotion.squeeze(0))
                emotion = FloatTensor(emotion).to(device)

            try:
                log.debug("generating voice with embedding...")
                with no_grad():
                    x_tst = text.unsqueeze(0).to(device)
                    x_tst_lengths = LongTensor([text.size(0)]).to(device)
                    sid = LongTensor([index]).to(device) if index is not None else None
                    audio = net_g_ms.infer(x_tst, x_tst_lengths, sid=sid, noise_scale=noise_scale,
                                           noise_scale_w=noise_scale_w, length_scale=length_scale,
                                           emotion_embedding=emotion)[0][0, 0] \
                        .data.to(device).cpu().float().numpy()
                write(voice_path / filename, hps_ms.data.sampling_rate, audio)
                new_voice = Path(change_by_decibel(voice_path / filename, voice_path, tts_config.decibel))
                return new_voice
            except:
                traceback.print_exc()
                return "fail to generate voice"
            finally:
                torch.cuda.empty_cache()
    # TODO: voice conversion
    # else:
    #     # hubert
    #     from hubert_model import hubert_soft
    #     hubert = hubert_soft(hubert_path / hubert_file)
    #     if use_f0:
    #         audio, sampling_rate = librosa.load(
    #             audio_path, sr=hps_ms.data.sampling_rate, mono=True)
    #         audio16000 = librosa.resample(
    #             audio, orig_sr=sampling_rate, target_sr=16000)
    #     else:
    #         audio16000, sampling_rate = librosa.load(
    #             audio_path, sr=16000, mono=True)
    #
    #     print_speakers(speakers, escape)
    #     target_id = get_speaker_id('Target speaker ID: ')
    #     out_path = input('Path to save: ')
    #     length_scale, out_path = get_label_value(
    #         out_path, 'LENGTH', 1, 'length scale')
    #     noise_scale, out_path = get_label_value(
    #         out_path, 'NOISE', 0.1, 'noise scale')
    #     noise_scale_w, out_path = get_label_value(
    #         out_path, 'NOISEW', 0.1, 'deviation of noise')
    #
    #     from torch import inference_mode, FloatTensor
    #     import numpy as np
    #     with inference_mode():
    #         units = hubert.units(FloatTensor(audio16000).unsqueeze(
    #             0).unsqueeze(0)).squeeze(0).numpy()
    #         if use_f0:
    #             f0_scale, out_path = get_label_value(
    #                 out_path, 'F0', 1, 'f0 scale')
    #             f0 = librosa.pyin(audio, sr=sampling_rate,
    #                               fmin=librosa.note_to_hz('C0'),
    #                               fmax=librosa.note_to_hz('C7'),
    #                               frame_length=1780)[0]
    #             target_length = len(units[:, 0])
    #             f0 = np.nan_to_num(np.interp(np.arange(0, len(f0) * target_length, len(f0)) / target_length,
    #                                          np.arange(0, len(f0)), f0)) * f0_scale
    #             units[:, 0] = f0 / 10
    #
    #     stn_tst = FloatTensor(units)
    #     with no_grad():
    #         x_tst = stn_tst.unsqueeze(0)
    #         x_tst_lengths = LongTensor([stn_tst.size(0)])
    #         sid = LongTensor([target_id])
    #         audio = net_g_ms.infer(x_tst, x_tst_lengths, sid=sid, noise_scale=noise_scale,
    #                                noise_scale_w=noise_scale_w, length_scale=length_scale)[0][0, 0].data.float().numpy()


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
        if threshold < 0:
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
