import httpx
import time
import hashlib
import random
import json
import uuid
import hmac
import base64
from ffmpy import FFmpeg
import os
from .text import text_to_sequence
from .commons import intersperse
from torch import no_grad, LongTensor
from .utils import *
from utils.log import logger as log
from .config import tts_config
from typing import List, Tuple, Dict
from sys import maxsize


def character_list(tts_gal):
    valid_names = []
    for names, model in tts_gal.items():
        if isinstance(names, str):
            valid_names.append(names)
        elif isinstance(names, tuple):
            valid_names.extend(names)
    return valid_names


def check_character(name, valid_names, tts_gal):
    index = None
    config_file = ""
    model_file = ""
    for names, model in tts_gal.items():
        if names in valid_names and \
                ((isinstance(names, str) and names == name) or
                 ((isinstance(names, tuple) and name in names))):
            config_file = model[0] + ".json"
            model_file = model[0] + ".pth"
            index = None if len(model) == 1 else int(model[1])
            break
    return config_file, model_file, index


def load_language(hps_ms):
    try:
        return hps_ms.language
    except:
        log.info("配置文件中缺少language项,将默认使用日语配置项")
        return "ja"


def load_symbols(hps_ms, lang, symbols_dict):
    try:
        symbols = hps_ms.symbols
    except:
        log.info("配置文件中缺失symbols项,建议手动添加")
        if lang in symbols_dict.keys():
            log.info("采用language指定的symbols项")
            symbols = symbols_dict[lang]
        else:
            log.info("该语言未有默认symbols项，将采用日语symbols")
            symbols = symbols_dict["ja"]
    return symbols


def get_text(text, hps, symbols, lang, cleaned=False):
    if cleaned:
        text_norm = text_to_sequence(text, symbols, [], lang)
    else:
        text_norm = text_to_sequence(
            text, symbols, hps.data.text_cleaners, lang)
    if hps.data.add_blank:
        text_norm = intersperse(text_norm, 0)
    text_norm = LongTensor(text_norm)
    return text_norm


def changeC2E(s: str):
    return s.replace("。", ".").replace("？", "?").replace("！", "!").replace("，", ",")


def changeE2C(s: str):
    return s.replace(".", "。").replace("?", "？").replace("!", "！").replace(",", "，")


async def translate_youdao(text: str, lang: str) -> Tuple[str, bool]:
    '''
    return 翻译结果(str)，是否删除该项翻译(bool)
    '''

    url = f"https://fanyi.youdao.com/translate_o?smartresult=dict&smartresult=rule"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36",
        "Cookie": "OUTFOX_SEARCH_USER_ID=467129664@10.169.0.102; JSESSIONID=aaaejjt9lMzrAgeDsHrWx;OUTFOX_SEARCH_USER_ID_NCOO=1850118475.9388125; ___rl__test__cookies=1632381536261",
        "Referer": "https://fanyi.youdao.com/"
    }
    ts = str(int(time.time() * 1000))
    salt = ts + str(random.randint(0, 9))
    temp = "fanyideskweb" + text + salt + "Ygy_4c=r#e#4EX^NUGUc5"
    md5 = hashlib.md5()
    md5.update(temp.encode())
    sign = md5.hexdigest()
    data = {
        "i": text,
        "from": "Auto",
        "to": lang,
        "smartresult": "dict",
        "client": "fanyideskweb",
        "salt": salt,
        "sign": sign,
        "lts": ts,
        "bv": "5f70acd84d315e3a3e7e05f2a4744dfa",
        "doctype": "json",
        "version": "2.1",
        "keyfrom": "fanyi.web",
        "action": "FY_BY_REALTlME",
    }
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, data=data, headers=headers)
            result = json.loads(resp.content)
            if resp.status_code != 200:
                log.error(f"有道翻译错误代码 {resp.status_code},{resp.text}")
                return "", False
        res = ""
        for s in result['translateResult'][0]:
            res += s['tgt']
        return res, False
    except Exception as e:
        log.error(f"有道翻译 {type(e)} {e}")
        return "", False


async def translate_baidu(text: str, lang: str) -> Tuple[str, bool]:
    '''
    return 翻译结果(str)，是否删除该项翻译(bool)
    '''
    lang_change = {
        "zh-CHS": "zh",
        "ja": "jp",
        "ko": "kor",
        "fr": "fra",
        "es": "spa",
        "vi": "vie",
        "ar": "ara"
    }
    if lang in lang_change.keys():
        lang = lang_change[lang]
    salt = str(round(time.time() * 1000))
    appid = tts_config.baidu_tran_appid
    apikey = tts_config.baidu_tran_apikey
    sign_raw = appid + text + salt + apikey
    sign = hashlib.md5(sign_raw.encode("utf8")).hexdigest()
    params = {
        "q": text,
        "from": "auto",
        "to": lang,
        "appid": appid,
        "salt": salt,
        "sign": sign,
    }
    url = "https://fanyi-api.baidu.com/api/trans/vip/translate"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params)
            result = resp.json()
            status_code = resp.status_code
            if status_code != 200:
                log.error(f"百度翻译错误代码 {resp.status_code},{resp.text}")
                return "", False
        if "error_code" in result.keys():
            log.error(f"百度翻译 {result['error_code']}:{result['error_msg']}")
            if result['error_code'] == "54004":
                return "", True
            return "", False
        return result["trans_result"][0]["dst"], False
    except Exception as e:
        log.error(f"百度翻译 {type(e)} {e}")
        return "", False


async def translate_tencent(text: str, lang: str) -> Tuple[str, bool]:
    '''
    return 翻译结果(str)，是否删除该项翻译(bool)
    '''

    async def getSign(action: str, params: dict) -> str:
        common = {
            "Action": action,
            "Region": tts_config.tencent_tran_region,
            "Timestamp": int(time.time()),
            "Nonce": random.randint(1, maxsize),
            "SecretId": tts_config.tencent_tran_secretid,
            "Version": "2018-03-21",
        }
        params.update(common)
        sign_str = "POSTtmt.tencentcloudapi.com/?"
        sign_str += "&".join("%s=%s" % (k, params[k]) for k in sorted(params))
        secret_key = tts_config.tencent_tran_secretkey
        sign_str = bytes(sign_str, "utf-8")
        secret_key = bytes(secret_key, "utf-8")
        hashed = hmac.new(secret_key, sign_str, hashlib.sha1)
        signature = base64.b64encode(hashed.digest())
        signature = signature.decode()
        return signature

    async def LanguageDetect(text: str) -> Tuple[str, bool]:
        url = "https://tmt.tencentcloudapi.com"
        params = {
            "Text": text,
            "ProjectId": 0,
        }
        params["Signature"] = await getSign("LanguageDetect", params)
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, data=params)
                status_code = resp.status_code
                if status_code != 200:
                    log.error(f"腾讯语种识别错误代码 {resp.status_code},{resp.text}")
                    return "", False
                res = resp.json()["Response"]
            if "Error" in res.keys():
                log.error(f"腾讯语种识别 {res['Error']['Code']} {res['Error']['Message']}")
                if res['Error']['Code'] == "FailedOperation.NoFreeAmount" or \
                        res['Error']['Code'] == "FailedOperation.ServiceIsolate":
                    return "", True
                return "", False
            return res["Lang"], False
        except Exception as e:
            log.error(f"腾讯语种识别 {type(e)} {e}")
            return "", False

    lang_change = {
        "zh-CHS": "zh"
    }
    if lang in lang_change.keys():
        lang = lang_change[lang]
    source_lang, flag = await LanguageDetect(text)
    if not source_lang:
        return "", flag
    if source_lang == lang:
        return text, flag
    url = "https://tmt.tencentcloudapi.com"
    params = {
        "Source": source_lang,
        "SourceText": text,
        "Target": lang,
        "ProjectId": tts_config.tencent_tran_projectid
    }
    params["Signature"] = await getSign("TextTranslate", params)
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, data=params)
            status_code = resp.status_code
            if status_code != 200:
                log.error(f"腾讯翻译错误代码 {resp.status_code},{resp.text}")
                return "", False
            res = resp.json()["Response"]
        if "Error" in res.keys():
            log.error(f"腾讯翻译 {res['Error']['Code']} {res['Error']['Message']}")
            if res['Error']['Code'] == "FailedOperation.NoFreeAmount" or \
                    res['Error']['Code'] == "FailedOperation.ServiceIsolate":
                return "", True
            return "", False
        return res["TargetText"], False
    except Exception as e:
        log.error(f"腾讯翻译 {type(e)} {e}")
        return "", False


support_tran = {
    "youdao": translate_youdao,
    "baidu": translate_baidu,
    "tencent": translate_tencent
}


async def translate(tran_type: List[str], lock_tran_list: Dict[str, List[str]], text: str, lang: str) -> str:
    for tran in tran_type:
        if tran not in lock_tran_list["manual"] and tran not in lock_tran_list["auto"]:
            res, flag = await support_tran[tran](text, lang)
            if flag:
                lock_tran_list["auto"].append(tran)
            if res:
                break
    return res


def change_by_decibel(audio_path: str, output_dir: str, decibel):
    ext = os.path.basename(audio_path).strip().split('.')[-1]
    if ext not in ['wav', 'mp3']:
        raise Exception('format error')
    new_name = uuid.uuid4()
    ff = FFmpeg(inputs={'{}'.format(audio_path): None},
                outputs={os.path.join(output_dir,
                                      '{}.{}'.format(new_name, ext)): '-filter:a "volume={}dB" -loglevel quiet'.format(
                    decibel)})
    ff.run()
    os.remove(audio_path)
    return os.path.join(output_dir, '{}.{}'.format(new_name, ext))
