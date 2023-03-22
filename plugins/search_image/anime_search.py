from utils.http_utils import AsyncHttpx
from utils.tranlator import Translate

URL = "https://api.trace.moe/search?anilistInfo=true&url="


class Anime():
    @staticmethod
    async def _request(url: str) -> dict:
        aim = URL + url
        try:
            res = await AsyncHttpx.get(aim)
        except Exception:
            raise Exception("Request failed!")
        result = res.json()
        return result

    @classmethod
    async def search(cls, url: str) -> str:
        data = await cls._request(url)
        try:
            data = data["result"]
        except Exception:
            return "没有相似的结果呢..."

        d = dict()
        for i in range(3):
            if data[i]["anilist"]["title"]["native"] in d.keys():
                d[data[i]["anilist"]["title"]["native"]][0] += data[i]["similarity"]
            else:
                from_m = data[i]["from"] / 60
                from_s = data[i]["from"] % 60

                to_m = data[i]["to"] / 60
                to_s = data[i]["to"] % 60

                if not data[i]["episode"]:
                    n = 1
                else:
                    n = data[i]["episode"]

                d[Translate(data[i]["anilist"]["title"]["native"]).to_simple()] = [
                    data[i]["similarity"],
                    f"第{n}集",
                    f"约{int(from_m)}min{int(from_s)}s至{int(to_m)}min{int(to_s)}s处",
                ]

        result = sorted(d.items(), key=lambda x: x[1], reverse=True)
        t = 0
        msg0 = str()
        for i in result:
            t += 1
            s = "%.2f%%" % (i[1][0] * 100)
            msg0 = msg0 + (
                "\n——————————\n"
                f"({t}) Similarity: {s}\n"
                f"Name: {i[0]}\n"
                f"Time: {i[1][1]} {i[1][2]}"
            )

        return msg0
