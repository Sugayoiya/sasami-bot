import datetime
import json
from copy import deepcopy
from os.path import exists

import requests
from PIL import Image, ImageFont

from configs.path_config import TEXT_PATH, FONT_PATH, IMAGE_PATH
from utils.log import logger as log
from .config import Config
from .nintendo_utils import SplatoonUtils

config = Config()
# 品牌名称key
BRAND_NAME_KEY = 'CommonMsg/Gear/GearBrandName'
# 装备（头部）key
GEAR_NAME_HEAD_KEY = 'CommonMsg/Gear/GearName_Head'
# 装备（衣服）key
GEAR_NAME_CLOTHES_KEY = 'CommonMsg/Gear/GearName_Clothes'
# 装备（鞋子）key
GEAR_NAME_SHOE_KEY = 'CommonMsg/Gear/GearName_Shoes'
# 装备技能描述key
GEAR_POWER_DESC_KEY = 'CommonMsg/Gear/GearPowerExp'
# 装备技能key
GEAR_POWER_KEY = 'CommonMsg/Gear/GearPowerName'

gear_dict = {'HeadGear': GEAR_NAME_HEAD_KEY, 'ClothingGear': GEAR_NAME_CLOTHES_KEY, 'ShoesGear': GEAR_NAME_SHOE_KEY}
gear_pic_dict = {'HeadGear': 'Hed_', 'ClothingGear': 'Clt_', 'ShoesGear': 'Shs_'}

UNUSUAL_SKILL_KEY = 'UnusualGearSkill'
USUAL_SKILL_KEY = 'UsualGearSkill'


class Splatoon3:
    def __init__(self):
        self.splatoon3_ink_schedule_url = 'https://splatoon3.ink/data/schedules.json'
        self.splatoon3_ink_gear_shop_url = 'https://splatoon3.ink/data/gear.json'

        self.schedule_json_location = TEXT_PATH / "splatoon3" / "schedules.json"
        self.gear_json_location = TEXT_PATH / "splatoon3" / "gear.json"

        self.regular_schedules: list = []
        self.bankara_schedules: list = []
        self.x_schedules: list = []
        self.league_schedules: list = []
        self.regular_coop_schedules: list = []
        self.big_run_coop_schedules: list = []

        self.pickup_brand_gears: dict = {}
        self.limited_gears: list = []

        self.current_fest: str = ''

        self.CN_zh: dict = {}
        self.EU_en: dict = {}
        self.brand_traits: dict = {}

        self.font = ImageFont.truetype(
            str(FONT_PATH / "splatoon3" / "splatfontfont.otf"), 20)
        self.x_font = ImageFont.truetype(
            str(FONT_PATH / "splatoon3" / "test0.ttf"), 20)
        self.init_json()

    def init_json(self):
        log.debug('初始化 splatoon3.ink 的 json 文件')
        log.debug('初始化 schedules.json 文件')
        schedule_rst_json = self._get_schedule_data()

        log.debug('获取对战模式/地图信息')
        self.regular_schedules = schedule_rst_json['regularSchedules']['nodes']
        self.bankara_schedules = schedule_rst_json['bankaraSchedules']['nodes']
        self.x_schedules = schedule_rst_json['xSchedules']['nodes']
        self.league_schedules = schedule_rst_json['leagueSchedules']['nodes']
        self.regular_coop_schedules = schedule_rst_json['coopGroupingSchedule']['regularSchedules']['nodes']
        self.big_run_coop_schedules = schedule_rst_json['coopGroupingSchedule']['bigRunSchedules']['nodes']
        self.current_fest = schedule_rst_json['currentFest']

        log.debug('初始化 gear.json 文件')
        gear_shop_rst_json = self._get_gear_data()

        log.debug('获取装备信息')
        self.pickup_brand_gears = gear_shop_rst_json['gesotown']['pickupBrand']
        self.limited_gears = gear_shop_rst_json['gesotown']['limitedGears']

        log.debug('载入 CNzh.json 翻译文件')
        with open(config.cn_zh) as file:
            self.CN_zh = json.loads(file.read())
            log.debug('CN_zh 载入成功')
        log.debug('载入 EUen.json 翻译文件')
        with open(config.eu_en) as file:
            self.EU_en = json.loads(file.read())
            log.debug('EU_en 载入成功')
        log.debug('载入 brand_traits.json 文件')
        with open(config.brand_traits) as file:
            self.brand_traits = json.loads(file.read())
            log.debug('brand_traits 载入成功')

    def _get_schedule_data(self):
        if not exists(self.schedule_json_location) or not self._check_schedule_data():
            log.debug('schedules.json 文件不存在或已过期，重新获取')
            splatoon3_ink_schedule_res = requests.get(self.splatoon3_ink_schedule_url)
            if splatoon3_ink_schedule_res.status_code == 200:
                schedule_rst = splatoon3_ink_schedule_res.text
                schedule_rst_json = json.loads(schedule_rst)['data']
                with open(self.schedule_json_location, 'w+', encoding='utf-8') as file:
                    file.write(json.dumps(schedule_rst_json, indent=4))
                return schedule_rst_json

        with open(self.schedule_json_location, 'r') as file:
            return json.loads(file.read())

    def _get_gear_data(self):
        if not exists(self.gear_json_location) or not self._check_gear_data():
            log.debug('gear.json 文件不存在或已过期，重新获取')
            splatoon3_ink_gear_shop_res = requests.get(self.splatoon3_ink_gear_shop_url)
            if splatoon3_ink_gear_shop_res.status_code == 200:
                gear_shop_rst = splatoon3_ink_gear_shop_res.text
                gear_shop_rst_json = json.loads(gear_shop_rst)['data']
                with open(self.gear_json_location, 'w+', encoding='utf-8') as file:
                    file.write(json.dumps(gear_shop_rst_json, indent=4))
                return gear_shop_rst_json

        with open(self.gear_json_location, 'r') as file:
            return json.loads(file.read())

    def _check_gear_data(self) -> bool:
        """
        检查 gear.json 文件是否过期
        :return:
        """
        log.debug('检查 gear.json 文件是否过期')
        if not exists(self.gear_json_location):
            return False
        with open(self.gear_json_location, 'r') as file:
            gear_json = json.loads(file.read())
            sale_end_time_str = gear_json.get('gesotown', {}).get('pickupBrand', {}).get('saleEndTime', None)
            log.debug(f'特选商店的 saleEndTime 为 {sale_end_time_str}')
            if not sale_end_time_str:
                log.debug('特选商店的 saleEndTime 为空，gear.json 文件已过期')
                return False
            limited_gears_list = gear_json.get('gesotown', {}).get('limitedGears', [])
            if not limited_gears_list:
                log.debug('限定商店的 limitedGears 为空，gear.json 文件已过期')
                return False
            # 如果有一个限定品的结束时间小于当前时间，就返回False
            for i in limited_gears_list:
                limited_sale_end_time = i.get('saleEndTime', None)
                log.debug(f'普通商店的{i.get("id", None)} saleEndTime 为 {limited_sale_end_time}')
                if not limited_sale_end_time or \
                        SplatoonUtils.get_gmt_datetime(limited_sale_end_time) < datetime.datetime.now():
                    log.debug(
                        f'普通商店的{i.get("id", None)} saleEndTime 为空或 {limited_sale_end_time} 已过期，gear.json 文件已过期')
                    return False
            # 如果精选商品的结束时间小于当前时间，就返回False
            if SplatoonUtils.get_gmt_datetime(sale_end_time_str) < datetime.datetime.now():
                log.debug(f'特选商店的 saleEndTime {sale_end_time_str} 已过期，gear.json 文件已过期')
                return False
            return True

    def _check_schedule_data(self) -> bool:
        """
        检查 schedules.json 文件是否过期
        :return:
        """
        log.debug('检查 schedule.json 文件是否过期')
        if not exists(self.schedule_json_location):
            return False
        with open(self.schedule_json_location, 'r') as file:
            schedule_rst_json = json.loads(file.read())

            # 注释的暂时用不到, 不知道是什么数据
            self.regular_schedules = schedule_rst_json['regularSchedules']['nodes']
            self.bankara_schedules = schedule_rst_json['bankaraSchedules']['nodes']
            # self.x_schedules = schedule_rst_json['xSchedules']['nodes']
            # self.league_schedules = schedule_rst_json['leagueSchedules']['nodes']
            self.regular_coop_schedules = schedule_rst_json['coopGroupingSchedule']['regularSchedules']['nodes']
            # self.big_run_coop_schedules = schedule_rst_json['coopGroupingSchedule']['bigRunSchedules']['nodes']
            # self.current_fest = schedule_rst_json['currentFest']

        now = datetime.datetime.now()
        log.debug(f'当前时间为 {now}')
        log.debug('检查「涂地模式」数据是否过期')
        for index, i in enumerate(self.regular_schedules):
            # 如果当前时间在这个开始和结束时间段内,就返回True
            if SplatoonUtils.get_gmt_datetime(i['startTime']) < now < SplatoonUtils.get_gmt_datetime(i['endTime']):
                # 如果这个元素的index在倒数第二之前, 就返回True
                if index > len(self.regular_schedules) - 2:
                    log.debug(
                        f'当前index为 {index}, 涂地模式列表总长度为 {len(self.regular_schedules)}, 涂地模式数据已过期')
                    return False

        log.debug('检查「真格模式」数据是否过期')
        for index, i in enumerate(self.bankara_schedules):
            # 如果当前时间在这个开始和结束时间段内,就返回True
            if SplatoonUtils.get_gmt_datetime(i['startTime']) < now < SplatoonUtils.get_gmt_datetime(i['endTime']):
                # 如果这个元素的index在倒数第二之前, 就返回True
                if index > len(self.bankara_schedules) - 2:
                    log.debug(
                        f'当前index为 {index}, 真格模式列表总长度为 {len(self.bankara_schedules)}, 真格模式数据已过期')
                    return False

        log.debug('检查「合作模式」数据是否过期')
        for index, i in enumerate(self.regular_coop_schedules):
            # 如果当前时间在这个开始和结束时间段内,就返回True
            if SplatoonUtils.get_gmt_datetime(i['startTime']) < now < SplatoonUtils.get_gmt_datetime(i['endTime']):
                # 如果这个元素的index在倒数第二之前, 就返回True
                if index > len(self.regular_coop_schedules) - 2:
                    log.debug(
                        f'当前index为 {index}, 合作模式列表总长度为 {len(self.regular_coop_schedules)}, 合作模式数据已过期')
                    return False

        return True

    def _handle_regular_schedules(self) -> list:
        """
        处理 regular_schedules 涂地模式数据
        :return: list
        """
        log.debug('处理 regular_schedules 涂地模式数据')
        regular_schedules_handled = []
        for i in self.regular_schedules:
            regular_schedule = dict()
            regular_schedule['startTime'] = SplatoonUtils.utc_to_gmt(i['startTime'])
            regular_schedule['endTime'] = SplatoonUtils.utc_to_gmt(i['endTime'])

            settings = list()
            setting = dict()
            setting['vsStages'] = i['regularMatchSetting']['vsStages']
            setting['rule'] = i['regularMatchSetting']['vsRule']
            settings.append(setting)

            regular_schedule['settings'] = settings
            regular_schedules_handled.append(regular_schedule)

        regular_schedules_handled = sorted(regular_schedules_handled, key=lambda x: x['startTime'])
        return regular_schedules_handled

    def _handle_bankara_schedules(self) -> list:
        """
        处理 bankara_schedules 真格模式数据
        :return: list
        """
        log.debug('处理 bankara_schedules 真格模式数据')
        bankara_schedules_handled = []
        for i in self.bankara_schedules:
            bankara_schedule = dict()
            bankara_schedule['startTime'] = SplatoonUtils.utc_to_gmt(i['startTime'])
            bankara_schedule['endTime'] = SplatoonUtils.utc_to_gmt(i['endTime'])

            settings = list()
            for j in i['bankaraMatchSettings']:
                setting = dict()
                setting['vsStages'] = j['vsStages']
                setting['rule'] = j['vsRule']
                setting['mode'] = j['mode']
                settings.append(settings)

            bankara_schedule['settings'] = settings
            bankara_schedules_handled.append(bankara_schedule)

        bankara_schedules_handled = sorted(bankara_schedules_handled, key=lambda x: x['startTime'])
        return bankara_schedules_handled

    def _handle_regular_coop_schedules(self) -> list:
        """
        处理 regular_coop_grouping_schedules 合作模式数据
        :return: list
        """
        log.debug('处理 regular_coop_schedules 合作模式数据')
        regular_coop_grouping_schedules_handled = []
        for i in self.regular_coop_schedules:
            regular_coop_grouping_schedule = dict()
            regular_coop_grouping_schedule['startTime'] = SplatoonUtils.utc_to_gmt(i['startTime'])
            regular_coop_grouping_schedule['endTime'] = SplatoonUtils.utc_to_gmt(i['endTime'])

            setting = dict()
            setting['coopStage'] = i['setting']['coopStage']
            setting['weapons'] = i['setting']['weapons']

            regular_coop_grouping_schedule['setting'] = setting
            regular_coop_grouping_schedules_handled.append(regular_coop_grouping_schedule)

        regular_coop_grouping_schedules_handled = sorted(regular_coop_grouping_schedules_handled,
                                                         key=lambda x: x['startTime'])
        return regular_coop_grouping_schedules_handled

    def _handle_gears(self):
        """
        处理 gears 鱿鱼须商店
        :return: 特选商店, 普通商店
        """
        # 特选商品
        pickup_brand_gears_handled = deepcopy(self.pickup_brand_gears)
        pickup_brand_gears_handled['saleEndTime'] = SplatoonUtils.utc_to_gmt(pickup_brand_gears_handled['saleEndTime'])
        for i in pickup_brand_gears_handled['brandGears']:
            i['saleEndTime'] = SplatoonUtils.utc_to_gmt(i['saleEndTime'])
        # 普通商品
        limited_gears_handled = deepcopy(self.limited_gears)
        for i in limited_gears_handled:
            i['saleEndTime'] = SplatoonUtils.utc_to_gmt(i['saleEndTime'])

        return pickup_brand_gears_handled, limited_gears_handled

    def get_regular_schedules(self) -> list:
        """
        获取涂地模式数据
        :return: list
        """
        if not self._check_schedule_data():
            self.init_json()
        return self._handle_regular_schedules()

    def get_bankara_schedules(self) -> list:
        """
        获取真格模式数据
        :return: list
        """
        if not self._check_schedule_data():
            self.init_json()
        return self._handle_bankara_schedules()

    def get_coop_schedules(self) -> list:
        """
        获取合作模式数据
        :return: list
        """
        if not self._check_schedule_data():
            self.init_json()
        return self._handle_regular_coop_schedules()

    def get_gears(self) -> tuple:
        """
        获取鱿鱼须商店数据
        :return: tuple
        """
        if not self._check_gear_data():
            self.init_json()
        # 处理商店数据
        pickup_gears, limited_gears = self._handle_gears()

        pickup_gears_pics = []
        limited_gears_pics = []

        # 处理特选商店数据
        for pick_up_gear in pickup_gears['brandGears']:
            pickup_gears_pics.append(self.get_gear_detail(pick_up_gear))

        # 处理普通商店数据
        for gear in limited_gears:
            limited_gears_pics.append(self.get_gear_detail(gear))

        return pickup_gears_pics, limited_gears_pics

    def get_brand_skills(self, brand_key: str, brand_name: str):
        """
        获取品牌容易出的技能key && 不容易出的技能key
        :param brand_name: 品牌中文名
        :param brand_key: 品牌key
        :return: tuple
        """
        # log.debug(f'当前特选商店品牌中文名为: {brand_name}')
        rst = {}
        pickup_gears_brand_pic_path = config.brand / (brand_key + '.png')
        log.debug(f'当前特选商店品牌图片路径为: {pickup_gears_brand_pic_path}')

        # 容易出的技能key && 不容易出的技能key
        pickup_gears_brand_skills = self.brand_traits['Traits'][brand_key]
        usual_skill_key = pickup_gears_brand_skills[USUAL_SKILL_KEY]
        unusual_skill_key = pickup_gears_brand_skills[UNUSUAL_SKILL_KEY]

        # 容易出的技能, 描述
        usual_skill = self.CN_zh[GEAR_POWER_KEY][usual_skill_key]
        usual_skill_desc = self.CN_zh[GEAR_POWER_DESC_KEY][usual_skill_key]
        # 不容易出的技能, 描述
        unusual_skill = self.CN_zh[GEAR_POWER_KEY][unusual_skill_key]
        unusual_skill_desc = self.CN_zh[GEAR_POWER_DESC_KEY][unusual_skill_key]
        log.debug(
            f'当前特选商店品牌中文名为 {brand_name}, 容易出现的技能为: {usual_skill}, 技能特性为: {usual_skill_desc} '
            f'不容易出现的技能为: {unusual_skill}, 技能特性为: {unusual_skill_desc}')
        return usual_skill_key, unusual_skill_key

    def get_gear_detail(self, gear):
        # 处理单件商品
        price = gear['price']
        # 售卖终止时间
        pickup_gears_sale_end_time = gear['saleEndTime']

        gear = gear['gear']
        # 处理品牌数据
        pickup_gears_brand = gear['brand']['name']
        pickup_gears_brand_key, pickup_gears_brand_cn = self.get_cn_name_by_en_name(BRAND_NAME_KEY, pickup_gears_brand)
        # 获取品牌容易/不容易出的技能
        usual_skill_key, unusual_skill_key = self.get_brand_skills(pickup_gears_brand_key, pickup_gears_brand_cn)
        diff = datetime.datetime.strptime(pickup_gears_sale_end_time, "%Y-%m-%d %H:%M:%S") - datetime.datetime.now()
        hours_remain = int(diff.total_seconds() / 3600)
        minutes_remain = int(diff.total_seconds() / 60)

        log.debug(f'售卖终止时间: {pickup_gears_sale_end_time}, 剩余售卖小时: {hours_remain}')
        date_remain_text = ''
        if hours_remain > 0:
            if hours_remain > 1:
                date_remain_text = f'{hours_remain} hours left'
            else:
                date_remain_text = f'{hours_remain} hour left'
        else:
            if minutes_remain > 1:
                date_remain_text = f'{minutes_remain} minutes left'
            else:
                date_remain_text = f'{minutes_remain} minute left'

        gear_type = gear['__typename']
        # 处理商品key && 名称
        gear_name_key, gear_name_cn = self.get_cn_name_by_en_name(gear_dict[gear_type], gear['name'])
        log.info(f'gear_name_key: {gear_name_key}, gear_name_cn: {gear_name_cn}')
        gear_pic_path = config.gear / (gear_pic_dict[gear_type] + f'{gear_name_key}.png')
        log.debug(f'特选商品名称: {gear_name_cn}, 特选商品价格: {price}, 特选商品图片路径: {gear_pic_path}')
        # 处理商品技能
        primary_gear_power_name = gear['primaryGearPower']['name']
        primary_gear_power_name_key, primary_gear_power_name_cn = \
            self.get_cn_name_by_en_name(GEAR_POWER_KEY, primary_gear_power_name)
        # 仅图片为Unknown, 所以放在最后处理
        primary_gear_power_desc = self.CN_zh[GEAR_POWER_DESC_KEY][primary_gear_power_name_key]
        if primary_gear_power_name_key == 'None':
            primary_gear_power_name_key = 'Unknown'
        primary_gear_power_pic_path = config.gear_power / (primary_gear_power_name_key + '.png')
        log.debug(
            f'装备主技能: {primary_gear_power_name_cn}, 主技能效果为: {primary_gear_power_desc} 图片路径: {primary_gear_power_pic_path}')
        skill_list = [primary_gear_power_name_key + '.png']

        # 处理商品副技能
        additional_gear_powers = gear['additionalGearPowers']
        additional_gear_power_nums = len(additional_gear_powers)
        log.debug(f'装备副技能数量: {additional_gear_power_nums}')
        for gear_power in additional_gear_powers:
            additional_gear_power_name = gear_power['name']
            additional_gear_power_name_key, additional_gear_power_name_cn = \
                self.get_cn_name_by_en_name(GEAR_POWER_KEY, additional_gear_power_name)
            additional_gear_power_desc = self.CN_zh[GEAR_POWER_DESC_KEY][additional_gear_power_name_key]
            # 仅图片为Unknown, 所以放在最后处理
            if additional_gear_power_name_key == 'None':
                additional_gear_power_name_key = 'Unknown'
            additional_gear_power_pic_path = config.gear_power / (additional_gear_power_name_key + '.png')
            log.debug(
                f'装备副技能: {additional_gear_power_name_cn}, 副技能效果为: {additional_gear_power_desc} 图片路径: {additional_gear_power_pic_path}')
            skill_list.append(additional_gear_power_name_key + '.png')

        return self.get_gear_pic(gear_pic_dict[gear_type] + gear_name_key + '.png', skill_list,
                                 pickup_gears_brand_key + '.png', usual_skill_key + '.png', unusual_skill_key + '.png',
                                 date_remain_text, str(price), gear_name_cn)

    def get_cn_name_by_en_name(self, en_key, name):
        """
        根据英文名获取中文名
        :param en_key: 英文名字典的键
        :param name: 英文名
        :return: 中文名
        """
        # log.debug(f"英文字典为: {self.gear_trans[en_key]}")
        for k, v in self.EU_en[en_key].items():
            if v == name:
                return k, self.CN_zh[en_key][k]
        return "None", self.CN_zh[en_key]["None"]

    def get_gear_pic(self, gear_key: str, skill_key_list: list[str], brand_key: str, usual_skill_key: str,
                     unusual_skill_key: str, date_remain: str, price: str, gear_name: str):
        # 一堆图片素材默认位置(后续重构
        back_ground_pic_path = IMAGE_PATH / "splatoon3" / "gesotown-tape-blob-bg.png"
        brand_ground_pic_path = IMAGE_PATH / "splatoon3" / "gesotown-brand-bg.png"
        brand = IMAGE_PATH / "splatoon3" / "brand"
        gear = IMAGE_PATH / "splatoon3" / "gear"
        skill = IMAGE_PATH / "splatoon3" / "skill"
        coin = IMAGE_PATH / "splatoon3" / "gesotown-coin.png"
        price_pic_path = IMAGE_PATH / "splatoon3" / "news-bg.jpg"

        back_ground = Image.open(back_ground_pic_path).convert('RGBA')

        # 装备 技能 品牌图片路径
        gear_pic_path = gear / gear_key
        skill_pic_path = [skill / i for i in skill_key_list]
        brand_pic_path = brand / brand_key
        usual_skill_pic_path = skill / usual_skill_key
        unusual_skill_pic_path = skill / unusual_skill_key

        # print("gear_pic_path:", gear_pic_path)

        # 装备 技能 品牌 背景图片预处理 resize
        gear_pic = Image.open(gear_pic_path).convert('RGBA')
        skill_list = [Image.open(i).convert('RGBA') for i in skill_pic_path]
        skill_resized = [i.resize((int(j * 0.40) for j in i.size), Image.ANTIALIAS) for i in skill_list]
        brand_pic = Image.open(brand_pic_path).convert('RGBA')
        brand_resized = brand_pic.resize((int(i * 0.70) for i in brand_pic.size), Image.ANTIALIAS)
        brand_ground_pic = Image.open(brand_ground_pic_path).convert('RGBA')
        brand_ground_pic = brand_ground_pic.resize(brand_resized.size, Image.ANTIALIAS)
        back_ground = back_ground.resize((int(i * 0.35) for i in back_ground.size), Image.ANTIALIAS)

        (back_w, back_h) = back_ground.size
        (g_w, g_h) = gear_pic.size

        coin_pic = Image.open(coin).convert('RGBA')
        coin_pic_resize = coin_pic.resize((int(i * 1.3) for i in coin_pic.size), Image.ANTIALIAS)
        price_pic = Image.open(price_pic_path).convert('RGBA')
        price_pic_resize = price_pic.resize((back_w - 30, 40), Image.ANTIALIAS)

        usual_skill_pic = Image.open(usual_skill_pic_path).convert('RGBA')
        usual_skill_resized = usual_skill_pic.resize((int(j * 0.40) for j in usual_skill_pic.size), Image.ANTIALIAS)
        unusual_skill_pic = Image.open(unusual_skill_pic_path).convert('RGBA')
        unusual_skill_resized = unusual_skill_pic.resize((int(j * 0.40) for j in unusual_skill_pic.size),
                                                         Image.ANTIALIAS)

        # 贴图
        # print("back_w, back_h:", back_w, back_h)
        back_ground.paste(gear_pic, (int(back_w / 2 - g_w / 2), int(back_h / 6)), gear_pic)
        (w, h) = back_ground.size
        # print(w,h)
        # print(len(skill_resized))

        w_unit = skill_resized[0].size[0]
        h_unit = skill_resized[0].size[1]

        skill_pic_can = Image.new('RGBA', (w_unit * len(skill_resized), h_unit))
        # print(skill_pic_can.size)

        for i in range(len(skill_resized)):
            skill_pic_can.paste(skill_resized[i], (0 + w_unit * i, 0), skill_resized[i])
        (s_w, s_h) = skill_pic_can.size
        # print(s_w, s_h)

        back_ground.paste(skill_pic_can, (int(back_w / 2 - s_w / 2), 190), skill_pic_can)
        brand_ground_pic.paste(brand_resized, (0, 0), brand_resized)
        back_ground.paste(brand_ground_pic, (int(back_w / 6 * 4), 10), brand_ground_pic)
        # 常见技能/少见技能
        back_ground.paste(usual_skill_resized, (int(back_w / 6 * 4), 50), usual_skill_resized)
        back_ground.paste(unusual_skill_resized, (int(back_w / 6 * 4 + usual_skill_resized.size[0]), 50),
                          unusual_skill_resized)

        SplatoonUtils.draw_text([gear_name], [(price_pic_resize.size[0] / 2 - 60, 10)], price_pic_resize, "white",
                                self.x_font)
        back_ground.paste(price_pic_resize, (int(back_w / 2 - price_pic_resize.size[0] / 2), 240), price_pic_resize)
        back_ground.paste(coin_pic_resize, (int(back_w / 4 * 1), 285), coin_pic_resize)

        SplatoonUtils.draw_text([date_remain], [(35, 20)], back_ground, "white", self.font)
        SplatoonUtils.draw_text([price], [(int(back_w / 5 * 2), 275)], back_ground, "white", self.font)

        # print(back_ground)
        # log.info(f'商品的图片为: {back_ground}')
        return back_ground
