""" from https://github.com/keithito/tacotron """

import re
import jieba
from pypinyin import load_phrases_dict
from unidecode import unidecode

from .cc_cedict_local import load as cc_cedict_local_load
from .kmandarin_8105_local import load as kmandarin_8105_local_load

'''
Cleaners are transformations that run over the input text at both training and eval time.

Cleaners can be selected by passing a comma-delimited list of cleaner names as the "cleaners"
hyperparameter. Some cleaners are English-specific. You'll typically want to use:
  1. "english_cleaners" for English text
  2. "transliteration_cleaners" for non-English text that can be transliterated to ASCII using
     the Unidecode library (https://pypi.python.org/pypi/Unidecode)
  3. "basic_cleaners" if you do not want to transliterate (in this case, you should also update
     the symbols in symbols.py to match your data).
'''

PHRASE_LIST = [
    "琴", "安柏", "丽莎", "凯亚", "芭芭拉", "迪卢克", "雷泽", "温迪", "可莉", "班尼特", "诺艾尔", "菲谢尔",
    "砂糖", "莫娜", "迪奥娜", "阿贝多", "罗莎莉亚", "优菈", "魈", "北斗", "凝光", "香菱", "行秋", "重云",
    "七七", "刻晴", "达达利亚", "钟离", "辛焱", "甘雨", "胡桃", "烟绯", "申鹤", "云堇", "夜兰", "神里绫华",
    "神里", "绫华", "枫原万叶", "枫原", "万叶", "宵宫", "早柚", "雷电将军", "九条裟罗", "九条", "裟罗", "珊瑚宫心海",
    "珊瑚宫", "心海", "托马", "荒泷", "一斗", "荒泷派", "五郎", "八重神子", "神子", "神里绫人", "绫人",
    "久岐忍", "鹿野院平藏", "平藏", "蒙德", "璃月", "稻妻", "北风的王狼", "风魔龙", "特瓦林", "若陀龙王", "龙脊雪山",
    "金苹果群岛", "渊下宫", "层岩巨渊", "奥赛尔", "七天神像", "钩钩果", "落落莓", "塞西莉亚花", "风车菊", "尘歌壶",
    "提瓦特", "明冠山地", "风龙废墟", "明冠峡", "坠星山谷", "果酒湖", "望风山地", "坎瑞亚", "须弥", "枫丹", "纳塔",
    "至冬", "丘丘人", "丘丘暴徒", "深渊法师", "深渊咏者", "盗宝团", "愚人众", "深渊教团", "骗骗花", "急冻树", "龙蜥",
    "鸣神岛", "神无冢", "八酝岛", "海祇岛", "清籁岛", "鹤观", "绝云间", "群玉阁", "南十字", "死兆星", "木漏茶室",
    "神樱",
    "鸣神大社", "天使的馈赠", "社奉行", "勘定奉行", "天领奉行", "夜叉", "风神", "岩神", "雷神", "风之神", "岩之神",
    "雷之神",
    "风神瞳", "岩神瞳", "雷神瞳", "摩拉克斯", "契约之神", "雷电影", "雷电真", "八重宫司", "宫司大人", "巴巴托斯",
    "玉衡星",
    "天权星", "璃月七星", "留云借风", "削月筑阳", "理水叠山", "请仙典仪"
]

cc_cedict_local_load()
kmandarin_8105_local_load()

for phrase in PHRASE_LIST:
    jieba.add_word(phrase)

load_phrases_dict({"若陀": [["rě"], ["tuó"]], "平藏": [["píng"], ["zàng"]],
                   "派蒙": [["pài"], ["méng"]], "安柏": [["ān"], ["bó"]],
                   "一斗": [["yī"], ["dǒu"]]
                   })

# Regular expression matching whitespace:
_whitespace_re = re.compile(r'\s+')


def lowercase(text):
    return text.lower()


def collapse_whitespace(text):
    return re.sub(_whitespace_re, ' ', text)


def convert_to_ascii(text):
    return unidecode(text)


def basic_cleaners(text):
    """Basic pipeline that lower cases and collapses whitespace without transliteration."""
    text = lowercase(text)
    text = collapse_whitespace(text)
    return text


def transliteration_cleaners(text):
    """Pipeline for non-English text that transliterates to ASCII."""
    text = convert_to_ascii(text)
    text = lowercase(text)
    text = collapse_whitespace(text)
    return text


def japanese_cleaners(text):
    from .japanese import japanese_to_romaji_with_accent
    text = japanese_to_romaji_with_accent(text)
    text = re.sub(r'([A-Za-z])$', r'\1.', text)
    return text


def japanese_cleaners2(text):
    return japanese_cleaners(text).replace('ts', 'ʦ').replace('...', '…')


def korean_cleaners(text):
    '''Pipeline for Korean text'''
    from .korean import latin_to_hangul, number_to_hangul, divide_hangul
    text = latin_to_hangul(text)
    text = number_to_hangul(text)
    text = divide_hangul(text)
    text = re.sub(r'([\u3131-\u3163])$', r'\1.', text)
    return text


def chinese_cleaners(text):
    '''Pipeline for Chinese text'''
    from .mandarin import number_to_chinese, chinese_to_bopomofo, latin_to_bopomofo
    text = number_to_chinese(text)
    text = chinese_to_bopomofo(text)
    text = latin_to_bopomofo(text)
    text = re.sub(r'([ˉˊˇˋ˙])$', r'\1。', text)
    return text


def zh_ja_mixture_cleaners(text):
    from .mandarin import chinese_to_romaji
    from .japanese import japanese_to_romaji_with_accent
    text = re.sub(r'\[ZH\](.*?)\[ZH\]',
                  lambda x: chinese_to_romaji(x.group(1)) + ' ', text)
    text = re.sub(r'\[JA\](.*?)\[JA\]', lambda x: japanese_to_romaji_with_accent(
        x.group(1)).replace('ts', 'ʦ').replace('u', 'ɯ').replace('...', '…') + ' ', text)
    text = re.sub(r'\s+$', '', text)
    text = re.sub(r'([^\.,!\?\-…~])$', r'\1.', text)
    return text


def sanskrit_cleaners(text):
    text = text.replace('॥', '।').replace('ॐ', 'ओम्')
    text = re.sub(r'([^।])$', r'\1।', text)
    return text


def cjks_cleaners(text):
    from .mandarin import chinese_to_lazy_ipa
    from .japanese import japanese_to_ipa
    from .korean import korean_to_lazy_ipa
    from .sanskrit import devanagari_to_ipa
    from .english import english_to_lazy_ipa
    text = re.sub(r'\[ZH\](.*?)\[ZH\]',
                  lambda x: chinese_to_lazy_ipa(x.group(1)) + ' ', text)
    text = re.sub(r'\[JA\](.*?)\[JA\]',
                  lambda x: japanese_to_ipa(x.group(1)) + ' ', text)
    text = re.sub(r'\[KO\](.*?)\[KO\]',
                  lambda x: korean_to_lazy_ipa(x.group(1)) + ' ', text)
    text = re.sub(r'\[SA\](.*?)\[SA\]',
                  lambda x: devanagari_to_ipa(x.group(1)) + ' ', text)
    text = re.sub(r'\[EN\](.*?)\[EN\]',
                  lambda x: english_to_lazy_ipa(x.group(1)) + ' ', text)
    text = re.sub(r'\s+$', '', text)
    text = re.sub(r'([^\.,!\?\-…~])$', r'\1.', text)
    return text


def cjke_cleaners(text):
    from .mandarin import chinese_to_lazy_ipa
    from .japanese import japanese_to_ipa
    from .korean import korean_to_ipa
    from .english import english_to_ipa2
    text = re.sub(r'\[ZH\](.*?)\[ZH\]', lambda x: chinese_to_lazy_ipa(x.group(1)).replace(
        'ʧ', 'tʃ').replace('ʦ', 'ts').replace('ɥan', 'ɥæn') + ' ', text)
    text = re.sub(r'\[JA\](.*?)\[JA\]', lambda x: japanese_to_ipa(x.group(1)).replace('ʧ', 'tʃ').replace(
        'ʦ', 'ts').replace('ɥan', 'ɥæn').replace('ʥ', 'dz') + ' ', text)
    text = re.sub(r'\[KO\](.*?)\[KO\]',
                  lambda x: korean_to_ipa(x.group(1)) + ' ', text)
    text = re.sub(r'\[EN\](.*?)\[EN\]', lambda x: english_to_ipa2(x.group(1)).replace('ɑ', 'a').replace(
        'ɔ', 'o').replace('ɛ', 'e').replace('ɪ', 'i').replace('ʊ', 'u') + ' ', text)
    text = re.sub(r'\s+$', '', text)
    text = re.sub(r'([^\.,!\?\-…~])$', r'\1.', text)
    return text


def cjke_cleaners2(text):
    from .mandarin import chinese_to_ipa
    from .japanese import japanese_to_ipa2
    from .korean import korean_to_ipa
    from .english import english_to_ipa2
    text = re.sub(r'\[ZH\](.*?)\[ZH\]',
                  lambda x: chinese_to_ipa(x.group(1)) + ' ', text)
    text = re.sub(r'\[JA\](.*?)\[JA\]',
                  lambda x: japanese_to_ipa2(x.group(1)) + ' ', text)
    text = re.sub(r'\[KO\](.*?)\[KO\]',
                  lambda x: korean_to_ipa(x.group(1)) + ' ', text)
    text = re.sub(r'\[EN\](.*?)\[EN\]',
                  lambda x: english_to_ipa2(x.group(1)) + ' ', text)
    text = re.sub(r'\s+$', '', text)
    text = re.sub(r'([^\.,!\?\-…~])$', r'\1.', text)
    return text


def thai_cleaners(text):
    from .thai import num_to_thai, latin_to_thai
    text = num_to_thai(text)
    text = latin_to_thai(text)
    return text


def shanghai_dialect_cleaners(text):
    from .shanghai_dialect import shanghai_dialect_to_ipa
    text = shanghai_dialect_to_ipa(text)
    text = re.sub(r'([^\.,!\?\-…~])$', r'\1.', text)
    return text


def chinese_dialect_cleaners(text):
    from .mandarin import chinese_to_ipa2
    from .japanese import japanese_to_ipa3
    from .shanghai_dialect import shanghai_dialect_to_ipa
    from .cantonese import cantonese_to_ipa
    from .english import english_to_lazy_ipa2
    from .ngu_dialect import ngu_dialect_to_ipa
    text = re.sub(r'\[ZH\](.*?)\[ZH\]',
                  lambda x: chinese_to_ipa2(x.group(1)) + ' ', text)
    text = re.sub(r'\[JA\](.*?)\[JA\]',
                  lambda x: japanese_to_ipa3(x.group(1)).replace('Q', 'ʔ') + ' ', text)
    text = re.sub(r'\[SH\](.*?)\[SH\]', lambda x: shanghai_dialect_to_ipa(x.group(1)).replace('1', '˥˧').replace('5',
                                                                                                                 '˧˧˦').replace(
        '6', '˩˩˧').replace('7', '˥').replace('8', '˩˨').replace('ᴀ', 'ɐ').replace('ᴇ', 'e') + ' ', text)
    text = re.sub(r'\[GD\](.*?)\[GD\]',
                  lambda x: cantonese_to_ipa(x.group(1)) + ' ', text)
    text = re.sub(r'\[EN\](.*?)\[EN\]',
                  lambda x: english_to_lazy_ipa2(x.group(1)) + ' ', text)
    text = re.sub(r'\[([A-Z]{2})\](.*?)\[\1\]', lambda x: ngu_dialect_to_ipa(x.group(2), x.group(
        1)).replace('ʣ', 'dz').replace('ʥ', 'dʑ').replace('ʦ', 'ts').replace('ʨ', 'tɕ') + ' ', text)
    text = re.sub(r'\s+$', '', text)
    text = re.sub(r'([^\.,!\?\-…~])$', r'\1.', text)
    return text
