import base64
import configparser
import datetime
from io import BytesIO
from pathlib import Path
from typing import List

import requests
from PIL import Image, ImageDraw, ImageFont


class SplatoonUtils:

    @staticmethod
    def request_get(url: str):
        """
        @name：request_get
        @remark： 获取数据
        @return： 获取到的数据
        """
        res = requests.get(url, timeout=(10, 60))
        return res.text

    @staticmethod
    def get_config(path: Path, section: str, option: str) -> str:
        """
        @name：get_config
        @author： DrinkOolongTea
        @remark： 获取配置文件
        @param： path:配置文件路径 section:配置项名称 option:配置项key
        @return： 值
        """
        config = configparser.ConfigParser()
        config.read(path, encoding="utf-8")
        return config.get(section, option)

    @staticmethod
    def change_time_zone(time_str: str) -> str:
        """
        @name：change_time_zone
        @author： DrinkOolongTea
        @remark： 更改时区为UTC+8时区
        @param： time:当前时间
        @return： 更改时区后时间
        """
        time_str: str = datetime.datetime.strptime(time_str + str(datetime.datetime.today().year), "%b %d %H:%M %Y")
        time_str: str = (time_str + datetime.timedelta(hours=8)).strftime('%m-%d %H:%M')
        return time_str

    @staticmethod
    def battle_time() -> int:
        """
        @name：battle_time
        @author： DrinkOolongTea
        @remark： 截取以2为倍数的整数时间
        @return： 返回时间
        """
        curr_time = datetime.datetime.now()
        time_str = curr_time.strftime("%H")
        if int(time_str) % 2 > 0:
            return int(time_str) - 1
        else:
            return int(time_str)

    @staticmethod
    def draw_text(info: List, box: List, background_img: Image, color: str, font: ImageFont):
        """
        @name：draw_text
        @author： DrinkOolongTea
        @remark： 拼接文字图片
        @param： info: 文字list background_img:图片 color:颜色 font:字体路径
        @return： 拼接后图片
        """
        draw = ImageDraw.Draw(background_img)
        for i in range(len(info)):
            draw.text(box[i], str(info[i]), fill=color, font=font)

    @staticmethod
    def img_base64_bytes(image: Image, img_format: str) -> str:
        """
        @name：img_base64_str
        @author： DrinkOolongTea
        @remark： 将图片转为base64存储
        @param： image: 图片对象 img_format:图片格式
        @return： base64str
        """
        buf = BytesIO()
        image.save(buf, img_format)
        base64_str: str = "base64://" + base64.b64encode(buf.getbuffer()).decode()
        return buf

    @staticmethod
    def mode_dict(context: str) -> str:
        """
        @name：mode_dict
        @author： DrinkOolongTea
        @remark： splatoon2模式字典
        @param： 英文
        @return： 中文
        """
        d = {"Rainmaker": "魚", "Splat Zones": "區域", "Clam Blitz": "蛤蜊", "Tower Control": "塔"}
        return d[context]

    @staticmethod
    def save_bytes_file(filename: Path, b: bytes):
        """
        @name：push_league_battle
        @author： DrinkOolongTea
        @remark： 保存文件
        @param： filename: 文件路径, s:储存内容
        @return： 
        """
        f = open(filename, 'wb')
        f.write(b.getvalue())
        f.close()

    @staticmethod
    def paste_img(path: Path, info: List, box: List, background_img: Image):
        """
        @name：paste_img
        @author： DrinkOolongTea
        @remark： 拼接图片
        @param： path:图片源路径 info: 图片list  box: 文字位置, background_img:背景图片
        @return： 拼接后结果
        """
        for i in range(len(info)):
            img = Image.open(Path(path / Path((info[i]).replace(" ", "_") + ".png"))).convert(
                'RGBA')
            r, g, b, a = img.split()
            background_img.paste(img, box[i], mask=a)

    @staticmethod
    def read_bytes_file(filename: Path) -> bytes:
        """
        @name：push_league_battle
        @author： DrinkOolongTea
        @remark： 读取文件内容
        @param： filename: path 文件路径
        @return： 读取内容
        """
        f = open(filename, 'rb')
        b_io = BytesIO(f.read())
        f.close()
        base64_str: str = "base64://" + base64.b64encode(b_io.getbuffer()).decode()
        return base64_str

    @staticmethod
    def utc_to_gmt(utc_date_str: str) -> str:
        """
        utc时间转换为gmt时间
        :param utc_date_str: utc_date_str
        :return: local_date_str
        """
        utc_date = datetime.datetime.strptime(utc_date_str, "%Y-%m-%dT%H:%M:%SZ")
        local_date = utc_date + datetime.timedelta(hours=8)
        local_date_str = datetime.datetime.strftime(local_date, '%Y-%m-%d %H:%M:%S')
        return local_date_str

    @staticmethod
    def get_utc_datetime(utc_date_str: str) -> datetime:
        """
        utc时间转换为datetime
        :param utc_date_str: utc_date_str
        :return: local_date_str
        """
        utc_date = datetime.datetime.strptime(utc_date_str, "%Y-%m-%dT%H:%M:%SZ")
        return utc_date

    @staticmethod
    def get_gmt_datetime(utc_date_str: str) -> datetime:
        """
        utc时间转换为datetime
        :param utc_date_str: utc_date_str
        :return: local_date_str
        """
        utc_date = datetime.datetime.strptime(utc_date_str, "%Y-%m-%dT%H:%M:%SZ")
        gmt_date = utc_date + datetime.timedelta(hours=8)
        return gmt_date
