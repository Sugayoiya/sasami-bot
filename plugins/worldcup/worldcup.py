import datetime
import re
import uuid
from itertools import groupby

import requests

headers = {
    'User-Agent': 'Coral/2.2.0 (com.nintendo.znca; build:1999; iOS 15.5.0) Alamofire/5.4.4',
    'Accept': 'application/json',
    'Content-Type': 'application/json; charset=utf-8',
    'Connection': 'Keep-Alive',
    'Accept-Encoding': 'gzip',
}

iptv = 'https://raw.githubusercontent.com/youshandefeiyang/IPTV/main/main/IPTV.m3u'


class WorldCup:
    @staticmethod
    def _init_iptv() -> dict:
        iptv_map = dict()
        selected_map = dict()
        res = requests.get(iptv, headers=headers)
        for i in res.text.split('#EXTINF:-1'):
            temp = i.split('\r\n')
            if len(temp) > 2:
                desc = temp[0].strip().split(',')
                iptv_map[desc[-1]] = temp[1]
        r = re.compile('[抖音｜咪咕]')
        for k, v in iptv_map.items():
            if r.search(k):
                selected_map[k] = v
        return selected_map

    def echo(self) -> str:
        return '\r\n'.join([f"{k}, {v}" for k, v in self._init_iptv().items()])

    @staticmethod
    def get_urls(days: list) -> list:
        if not days:
            today = datetime.datetime.today()
            yesterday = today - datetime.timedelta(days=1)
            days = [yesterday.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')]
        base_url = 'https://tiyu.baidu.com/api/match/%E4%B8%96%E7%95%8C%E6%9D%AF/live/date/{}/direction/after'

        urls = []
        for day in days:
            urls.append(base_url.format(day))
        return urls

    @staticmethod
    def parse_data(data: dict) -> dict:
        d = {}
        name1 = data['leftLogo']['name']
        name2 = data['rightLogo']['name']
        score1 = '' if data['leftLogo']['score'] == '-' else data['leftLogo']['score']
        score2 = '' if data['rightLogo']['score'] == '-' else data['rightLogo']['score']
        d['summary'] = f'{name1} VS {name2} - {score1} : {score2}' if score1 and score2 else f'{name1} VS {name2}'
        d['summary'] += f'\n{data["matchName"]}'
        d['dtstart'] = datetime.datetime.strptime(
            data['startTime'], '%Y-%m-%d %H:%M:%S')
        d['dtend'] = d['dtstart'] + datetime.timedelta(hours=2)
        d['description'] = data['matchName']
        d['uid'] = str(uuid.uuid4())
        return d

    def get_events(self, urls: list) -> list:
        events = []
        for url in urls:
            resp = requests.get(url)
            for data in resp.json()['data'][0]['list']:
                event_data = self.parse_data(data)
                events.append(event_data)
        return events

    @staticmethod
    def get_rst(dict_data: list[dict]) -> str:
        rst = []
        for desc, group in groupby(dict_data, lambda x: x['description']):
            r = ''
            r += f'【{desc}】\n'
            schedule_data = []
            for schedule in group:
                s = '{} - {}'.format(schedule['summary'].split('\n')[0],
                                     schedule['dtstart'].strftime("%m/%d/%Y, %H:%M:%S"))
                schedule_data.append(s)
            r += '\n'.join(schedule_data)
            rst.append(r)
        return '\n'.join(rst)

    def schedule(self, cmd: str):
        days = []
        data = self.get_events(self.get_urls(days))
        return self.get_rst(data)
