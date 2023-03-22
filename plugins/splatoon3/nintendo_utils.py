import base64
import datetime
from io import BytesIO
from typing import List

from PIL import Image, ImageDraw, ImageFont


class SplatoonUtils:

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
