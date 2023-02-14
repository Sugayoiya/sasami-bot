import json
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict
from typing import List, Literal, Optional, Union

from nonebot import get_driver
from nonebot.log import logger
from nonebot.utils import escape_tag
from playwright.async_api import Page, Route, async_playwright
from typing_extensions import Self

from configs.path_config import TEXT_PATH

driver = get_driver()

SESSION_TOKEN_KEY = "__Secure-next-auth.session-token"


class Config:
    def __init__(self):
        self.chatgpt_session_token: str = ""
        self.chatgpt_account: str = ""
        self.chatgpt_password: str = ""
        self.chatgpt_cd_time: int = 30
        self.chatgpt_proxies: Optional[str] = None
        self.chatgpt_refresh_interval: int = 30
        self.chatgpt_command: Union[str, List[str]] = ""
        self.chatgpt_to_me: bool = True
        self.chatgpt_timeout: int = 30
        self.chatgpt_api: str = "https://chat.openai.com/"
        self.chatgpt_image: bool = False
        self.chatgpt_image_width: int = 500
        self.chatgpt_priority: int = 999
        self.chatgpt_block: bool = True
        self.chatgpt_private: bool = True
        self.chatgpt_scope: Literal["private", "public"] = "private"
        self.chatgpt_data: Path = TEXT_PATH / "chatgpt_bak"
        self.chatgpt_max_rollback: int = 5
        self.chatgpt_detailed_error: bool = False

        self.init_config()

        a = "eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIn0..AEc24SZk7WVhgJuk.AcCQal-qrMg9ruUkfDAOhdLAl4NKsYDaHl0w8zShNcPVDzYIXYdt8H0ERZHEhTZUJe1jNqJZy6PUizl4Ftcn3WImVKJsP0znulC1-_MaH0N6YcS-QhuTqSUPU6KVWPTOPz5Jco_q-5VdQw61zFPTXpXHlmWOq7PGGuva2jKEniu2_PFO-S6IN69D4OGXibPcvcNGviV-DGLEL8tdEBqoJk3J1jyd8laPbZwSwPIRDUaTUha36GK4iY_-DtDozjlN7GUzWmzs8WWmU4P2YFk_mJI7GCel3Utn0_gmbopqN6szk0E_bcjOWa01gSR2ouwrKNS4BrT0T9TbQx2wnFWI5whJi0g6w7vioZWLWGEUdUw-naO2qpu__39hvLzBohmm3ylwnTgPUnUq0P0NpyBwsMbb-VllEMZ4kipBVGOQqZHhd8dDXmT12ME9-Pn_U7Ke4KALMm2X9BtewfWt8_inkh2z8UA-M2IKT-jsXRzCUD14JanQrfQMHoMrwuHRGT4mXaw6Geo3yCZi11hvMaFki2oLAexGz6jMWmgCv9OCFLYFaEwDESFczk_eDczAN7UIPzdGxZOr4L1i7r_ktTdzsOhszRX1AbIHlfC3L4rRCkwTPVq60XaIDVR2JVzCvKqp5MdYugb4z1sAB5-Jn2SJ_Vo9MovWmrnK36eLcoruGrKg6ONIJUsMTU8P4OqmGH_ClzwzFLGf7TQAoLv5dvJs2jHcV7p_6n9F0jaONBczA3-aHaAdFs89QLhvnMuheDXezE7YzeRoGfHCPjEk2jE9mOZBF0ZCbHKP-18NTbk1KY6szeIt9HDXlreukraNw4uhk21yyPSKmKHTWG-1Xf-t_zOUerTBFrDUXsp3GNTM2QJ4940F2i1RxE0wg3pe27uDIqnMm3UaYVly_uxYTXKcsKuf-jYgXUZ6VX86atKPctW1u8LUL0zBNZIDqOM8jFzom3jiQSNuHeAasKJ9pIPWQbGXgS94mr37YrefEIKSh929crmrfnVmvsuRbqSjbWN5nXeiqeuNf9CP-_vQwTKeFX1ws7xs2ZTO0oL8HcTIrQ1c9etgs9KnqvgKa0xV1pZt104KIgIQy0wQgiR00BSvnruNxMMw4Nm6A6IKGyZq15S3-nTo_r0b7acZvI53A7R0xEgP1N-Ei41Hs7Z3Pt7WJEFA2JfXIU9ieF923uz3OHe59JsS_FwrjfDGVolXI-kSx6OBD0LSBIi46Gd64dljC_0loUk-MFdypUdmSDjgvNOG1zAQeCVBdYl3-Md527IJuOTZ6vr96HCjuMuogc6mPLEsryU_fRL8itkpvtTHAAp8J1B2VhDKaFRaSFwyrlqIxWAyq64HSTC6VlEU8q5thsRGfyR35xnRVpsvXJQu3DktNreo85lGTlUyOSXICli6Omv6opX9zF5Kzq0DOtd9PDA3AubAh-Uj7jzsVCPVSsvjQMGERcgTdl9IsjqYVIPmV-36wsmK3M2SBjPJzMJXzD_VnDLJy6HrzKKn4SKsy8M3RqS3b-0NjyJVF4Zg-EQ-bAYLMPgjmti4f_M1reO1LOuT3sbKJrX9Wr3CB8i8ZyCEv60zNK-KwnMBmrqioADouAMd5EiQQaAs4owrHOMVeMo4h1_0er2WVxcqK8bgPjSSoJhUOlx3zK31E3tcdC38EUCuMTOcoBcH8536QTENHTcHBil4Dt2aHoWLpC2Zk_1-pfJSrlALY7R5LBvhRwRKEIk6kI7X2ueABKJNgLy6JqtdcGCtrZfruu1XmtG1eXpgMKby-W1WnFqR4pbaTmzHGSmMyijRqwa1SSlIY3WbZgMJbT6dRYEAVp4rfGQq99kra1P2orXgnHqlgnd8wFDG4vcf_gEskr18rZz1k13MtA_wBles_lkY4n6V-ggPn_BG-E625QGnCu0h3W1fQfoP9AnvW4RzAVWz4FN4-h5FmiOcqu8BPlFGlYS-ku7JHyOkEkqtIHaV9T7Hx6OQSzPOoAhLQg0e4mq9eNH1G--Imm_kzVSvqTxayTns-wgR6Ote42m59hMsiUf9YMLlTxGyiioD_JZQC5B5Gpp0hNC1NKFFDOMLT6Lmi1JzKW6gWClSlIVqpEIYjbBm4W3j_a0R_QcMpeC849EZ0cxwbl0PhzSSfTInAJKcpxlyFoycEMA8q6TD4egP08SyGKdRTdnWv1mg6kPQYNaaN56K9PqBFdMqwcioukyzHU1T6CrkzqY04IwbkHNWel1FN3aRp9wB2fCd0nngBouBmfcso_jqL4H-EscwPO3Ip21WWwLesfUJODIQ70Mb1EL53py62s98Y_ThGV-EL40Ht2YOGmhPCONOrmTM_EIfadA_SBHOqznCq4zMQKk3qDiVoW25hWOLGRs5d5hQPCAIl_XnKFQK2N-fPI8kg6ZYCmfehYO7O-_re2Jpoce2dAvLgc22aK5OdHm__ytm04dGnOqkqOUIqhzuBu0GI1zxynvUWxvDAauw9ryoTSvMBEXhGXi5f6HJc0x9e4IHJhVI-46nJMI34DU-abjMS_7696l8WCxhAu0Gcn6iUDnqqVIV0RWB4xzvyoaV3SdS_s0Nm3v7r98AkEnO44nmMrJkudfApV5dzo6rCRP02Y-mEYkdAzLo5R2kxIZjo3EoNwTXTv5vhfx1G-l6_bxbNewN2AYy2MFpBHroApU0_90ufJmnCehZdADS6koxbJdJHw.Kyyr1hvSeFFbRy7gQBd5Tw"

    # 读取config_path的config.json文件，设置config的值
    def init_config(self) -> None:
        # 如果chatgpt_path文件路径不存在则创建，如果存在则读取配置
        if not self.chatgpt_data.exists():
            self.chatgpt_data.mkdir(parents=True)
        if (self.chatgpt_data / "config.json").exists():
            with open(self.chatgpt_data / "config.json", "r", encoding="utf-8") as f:
                config = json.load(f)
                self.chatgpt_account = config["chatgpt_account"]
                self.chatgpt_password = config["chatgpt_password"]
                self.chatgpt_proxies = config["chatgpt_proxies"]
                self.chatgpt_session_token = config["chatgpt_session_token"]
        else:
            with open(self.chatgpt_data / "config.json", "w", encoding="utf-8") as f:
                config = {
                    "chatgpt_account": "",
                    "chatgpt_password": "",
                    "chatgpt_proxies": "",
                    "chatgpt_session_token": "",
                }
                json.dump(config, f, ensure_ascii=False, indent=4)


class Chatbot:
    def __init__(
            self,
            *,
            token: str = "",
            account: str = "",
            password: str = "",
            api: str = "https://chat.openai.com/",
            proxies: Optional[str] = None,
            timeout: int = 10,
    ) -> None:
        self.session_token = token
        self.account = account
        self.password = password
        self.api_url = api
        self.proxies = proxies
        self.timeout = timeout
        self.content = None
        self.parent_id = None
        self.conversation_id = None
        self.browser = None
        self.playwright = async_playwright()
        if self.session_token:
            self.auto_auth = False
        elif self.account and self.password:
            self.auto_auth = True
        else:
            raise ValueError("至少需要配置 session_token 或者 account 和 password")

    async def playwright_start(self):
        """启动浏览器，在插件开始运行时调用"""
        playwright = await self.playwright.start()
        try:
            self.browser = await playwright.firefox.launch(
                headless=True,
                proxy={"server": self.proxies} if self.proxies else None,  # your proxy
            )
        except Exception as e:
            logger.opt(exception=e).error("playwright未安装，请先在shell中运行playwright install")
            return
        ua = f"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:72.0) Gecko/20100101 Firefox/{self.browser.version}"
        self.content = await self.browser.new_context(user_agent=ua)
        await self.set_cookie(self.session_token)

    async def set_cookie(self, session_token: str):
        """设置session_token"""
        self.session_token = session_token
        await self.content.add_cookies(
            [
                {
                    "name": SESSION_TOKEN_KEY,
                    "value": session_token,
                    "domain": "chat.openai.com",
                    "path": "/",
                }
            ]
        )

    @driver.on_shutdown
    async def playwright_close(self):
        """关闭浏览器"""
        await self.content.close()
        await self.browser.close()
        await self.playwright.__aexit__()

    def __call__(
            self, conversation_id: Optional[str] = None, parent_id: Optional[str] = None
    ) -> Self:
        self.conversation_id = conversation_id[-1] if conversation_id else None
        self.parent_id = parent_id[-1] if parent_id else self.id
        return self

    @property
    def id(self) -> str:
        return str(uuid.uuid4())

    def get_payload(self, prompt: str) -> Dict[str, Any]:
        return {
            "action": "next",
            "messages": [
                {
                    "id": self.id,
                    "role": "user",
                    "content": {"content_type": "text", "parts": [prompt]},
                }
            ],
            "conversation_id": self.conversation_id,
            "parent_message_id": self.parent_id,
            "model": "text-davinci-002-render",
        }

    @asynccontextmanager
    async def get_page(self):
        """打开网页，这是一个异步上下文管理器，使用async with调用"""
        page = await self.content.new_page()
        js = "Object.defineProperties(navigator, {webdriver:{get:()=>undefined}});"
        await page.add_init_script(js)
        await page.goto("https://chat.openai.com/chat")
        yield page
        await page.close()

    async def get_chat_response(self, prompt: str) -> str:
        async with self.get_page() as page:
            await page.wait_for_load_state("domcontentloaded")
            if not await page.locator("text=OpenAI Discord").is_visible():
                await self.get_cf_cookies(page)
            logger.debug("正在发送请求")

            async def change_json(route: Route):
                await route.continue_(
                    post_data=json.dumps(self.get_payload(prompt)),
                )

            await self.content.route(
                "https://chat.openai.com/backend-api/conversation", change_json
            )
            await page.wait_for_load_state("domcontentloaded")
            await page.wait_for_load_state("networkidle")
            session_expired = page.locator("button", has_text="Log in")
            if await session_expired.is_visible():
                logger.debug("检测到session过期")
                return "token失效，请重新设置token"
            next_botton = page.locator(
                ".btn.flex.justify-center.gap-2.btn-neutral.ml-auto"
            )
            if await next_botton.is_visible():
                logger.debug("检测到初次打开弹窗")
                await next_botton.click()
                await next_botton.click()
                await page.click(".btn.flex.justify-center.gap-2.btn-primary.ml-auto")
            async with page.expect_response(
                    "https://chat.openai.com/backend-api/conversation",
                    timeout=self.timeout * 1000,
            ) as response_info:
                textarea = page.locator("textarea")
                botton = page.locator("button").last
                logger.debug("正在等待回复")
                for _ in range(3):
                    await textarea.fill(prompt)
                    await page.wait_for_timeout(500)
                    if await botton.is_enabled():
                        await botton.click()
            response = await response_info.value
            if response.status == 429:
                return "请求过多，请放慢速度"
            if response.status == 403:
                await self.get_cf_cookies(page)
                return await self.get_chat_response(prompt)
            if response.status != 200:
                logger.opt(colors=True).error(
                    f"非预期的响应内容: <r>HTTP{response.status}</r> {escape_tag(response.text)}"
                )
                return f"ChatGPT 服务器返回了非预期的内容: HTTP{response.status}\n{response.text}"
            lines = await response.text()
            lines = lines.splitlines()
            data = lines[-4][6:]
            response = json.loads(data)
            self.parent_id = response["message"]["id"]
            self.conversation_id = response["conversation_id"]
            logger.debug("发送请求结束")
        return response["message"]["content"]["parts"][0]

    async def refresh_session(self) -> None:
        logger.debug("正在刷新session")
        if self.auto_auth:
            await self.login()
        else:
            async with self.get_page() as page:
                if not await page.locator("text=OpenAI Discord").is_visible():
                    await self.get_cf_cookies(page)
                await page.wait_for_load_state("domcontentloaded")
                session_expired = page.locator("text=Your session has expired")
                if await session_expired.count():
                    logger.opt(colors=True).error("刷新会话失败, session token 已过期, 请重新设置")
            cookies = await self.content.cookies()
            for i in cookies:
                if i["name"] == SESSION_TOKEN_KEY:
                    self.session_token = i["value"]
                    break
            logger.debug("刷新会话成功")

    async def login(self) -> None:
        from OpenAIAuth.OpenAIAuth import OpenAIAuth

        auth = OpenAIAuth(self.account, self.password, bool(self.proxies), self.proxies)  # type: ignore
        try:
            auth.begin()
        except Exception as e:
            if str(e) == "Captcha detected":
                logger.error("不支持验证码, 请使用 session token")
            raise e
        if not auth.access_token:
            logger.error("ChatGPT 登陆错误!")
        if auth.session_token:
            await self.set_cookie(auth.session_token)
        elif possible_tokens := auth.session.cookies.get(SESSION_TOKEN_KEY):
            if len(possible_tokens) > 1:
                await self.set_cookie(possible_tokens[0])
            else:
                try:
                    await self.set_cookie(possible_tokens)
                except Exception as e:
                    logger.opt(exception=e).error("ChatGPT 登陆错误!")
        else:
            logger.error("ChatGPT 登陆错误!")

    @staticmethod
    async def get_cf_cookies(page: Page) -> None:
        logger.debug("正在获取cf cookies")
        for _ in range(20):
            button = page.get_by_role("button", name="Verify you are human")
            if await button.count():
                await button.click()
            label = page.locator("label span")
            if await label.count():
                await label.click()
            await page.wait_for_timeout(1000)
            cf = page.locator("text=OpenAI Discord")
            if await cf.is_visible():
                break
        else:
            logger.error("cf cookies获取失败")
        logger.debug("cf cookies获取成功")
