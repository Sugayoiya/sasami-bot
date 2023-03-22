import os
from urllib.parse import urljoin
from urllib.request import pathname2url

from nonebot.adapters.onebot.v11.message import MessageSegment, Message
from PIL import Image
from loguru import logger

from configs.path_config import RESOURCE_PATH


class ResObj:
    def __init__(self, res_path):
        res_dir = os.path.expanduser(RESOURCE_PATH)
        fullpath = os.path.abspath(os.path.join(res_dir, res_path))
        if not fullpath.startswith(os.path.abspath(res_dir)):
            raise ValueError('Cannot access outside RESOUCE_DIR')
        self.__path = os.path.normpath(res_path)

    @property
    def path(self):
        """资源文件的路径，供Hoshino内部使用"""
        return os.path.join(RESOURCE_PATH, self.__path)

    @property
    def exist(self):
        return os.path.exists(self.path)


class ResImg(ResObj):
    @property
    def cqcode(self) -> MessageSegment:
        return MessageSegment.image(f'file:///{os.path.abspath(self.path)}')

    def open(self) -> Image:
        try:
            return Image.open(self.path)
        except FileNotFoundError:
            logger.error(f'缺少图片资源：{self.path}')
            raise


def get(path, *paths):
    return ResObj(os.path.join(path, *paths))


def img(path, *paths):
    return ResImg(os.path.join('img', path, *paths))
