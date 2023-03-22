import base64
import datetime
import hashlib
import json
import os
import re
import time
import urllib
from concurrent.futures import ThreadPoolExecutor

import requests
from bs4 import BeautifulSoup
from httpx import Response

from configs.path_config import TEXT_PATH
from utils.log import logger as log

# from utils.user_agent import get_user_agent_text

session = requests.Session()
thread_pool = ThreadPoolExecutor(max_workers=2)

A_VERSION = "0.3.1"
DEFAULT_USER_AGENT = 'Mozilla/5.0 (Linux; Android 11; Pixel 5) ' \
                     'AppleWebKit/537.36 (KHTML, like Gecko) ' \
                     'Chrome/94.0.4606.61 Mobile Safari/537.36'
ACC_LOCALE = 'en-US|US'
NSO_APP_VERSION = '2.4.0'
WEBVIEW_VERSION = '2.0.0-7070f95e'
F_GEN_URL = "https://api.imink.app/f"
SPLATNET3_URL = 'https://api.lp1.av5ja.srv.nintendo.net'
GRAPHQL_PATH = '/api/graphql'
BULLET_PATH = '/api/bullet_tokens'
S3S_NAMESPACE = 'b3a2dbf5-2c09-4792-b78c-00b548b70aeb'
SALMON_NAMESPACE = 'f1911910-605e-11ed-a622-7085c2057a9d'
SUPPORTED_KEYS = [
    'ignore_private',
    'ignore_private_jobs',
    'app_user_agent',
    'force_uploads',
]
# full GraphQL persisted query IDs see: https://github.com/samuelthomas2774/nxapi/discussions/11
TRANSLATE_RID = {
    "HomeQuery": "dba47124d5ec3090c97ba17db5d2f4b3",
    "LatestBattleHistoriesQuery": "0176a47218d830ee447e10af4a287b3f",
    "RegularBattleHistoriesQuery": "3baef04b095ad8975ea679d722bc17de",
    "BankaraBattleHistoriesQuery": "0438ea6978ae8bd77c5d1250f4f84803",
    "PrivateBattleHistoriesQuery": "8e5ae78b194264a6c230e262d069bd28",
    "XBattleHistoriesQuery": "6796e3cd5dc3ebd51864dc709d899fc5",
    "VsHistoryDetailQuery": "291295ad311b99a6288fc95a5c4cb2d2",
    "CoopHistoryQuery": "7edc52165b95dcb2b8a1c14c31e1d5b1",
    "CoopHistoryDetailQuery": "3cc5f826a6646b85f3ae45db51bd0707",
    "MyOutfitCommonDataEquipmentsQuery": "d29cd0c2b5e6bac90dd5b817914832f8"
}


def get_nintendo_web_text() -> Response:
    app_head = {
        'Upgrade-Insecure-Requests': '1',
        'Accept': '*/*',
        'DNT': '1',
        'X-AppColorScheme': 'DARK',
        'X-Requested-With': 'com.nintendo.znca',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-User': '?1',
        'Sec-Fetch-Dest': 'document'
    }
    app_cookies = {
        '_dnt': '1'  # Do Not Track
    }
    home = requests.get(SPLATNET3_URL, headers=app_head, cookies=app_cookies)
    return home


def get_nintendo_web_ver(res: Response):
    if res.status_code != 200:
        return WEBVIEW_VERSION
    soup = BeautifulSoup(res.text, "html.parser")
    main_js = soup.select_one("script[src*='static']")
    if not main_js:  # failed to parse html for main.js file
        return WEBVIEW_VERSION
    main_js_url = SPLATNET3_URL + main_js.attrs["src"]
    app_head = {
        'Accept': '*/*',
        'X-Requested-With': 'com.nintendo.znca',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'no-cors',
        'Sec-Fetch-Dest': 'script',
        'Referer': SPLATNET3_URL
    }
    app_cookies = {
        '_dnt': '1'
    }
    main_js_body = requests.get(main_js_url, headers=app_head, cookies=app_cookies)
    if main_js_body.status_code != 200:
        return WEBVIEW_VERSION
    pattern = r"\b(?P<revision>[0-9a-f]{40})\b[\S]*?void 0[\S]*?\"revision_info_not_set\"\}`,.*?=`(?P<version>\d+\.\d+\.\d+)-"
    match = re.search(pattern, main_js_body.text)
    if not match:
        return WEBVIEW_VERSION
    version, revision = match.group("version"), match.group("revision")
    ver_string = f"{version}-{revision[:8]}"
    return ver_string


def get_session_token(nso_app_version, session_token_code, auth_code_verifier):
    """Helper function for log_in()."""
    app_head = {
        'User-Agent': f'OnlineLounge/{nso_app_version} NASDKAPI Android',
        'Accept-Language': 'en-US',
        'Accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Content-Length': '540',
        'Host': 'accounts.nintendo.com',
        'Connection': 'Keep-Alive',
        'Accept-Encoding': 'gzip'
    }
    body = {
        'client_id': '71b963c1b7b6d119',
        'session_token_code': session_token_code,
        'session_token_code_verifier': auth_code_verifier.replace(b"=", b"")
    }
    url = 'https://accounts.nintendo.com/connect/1.0.0/api/session_token'
    r = session.post(url, headers=app_head, data=body)
    return json.loads(r.text)["session_token"]


def gen_graphql_body(sha256hash, name=None, value=None):
    """Generates a JSON dictionary, specifying information to retrieve, to send with GraphQL requests."""
    great_passage = {
        "extensions": {
            "persistedQuery": {
                "sha256Hash": sha256hash,
                "version": 1
            }
        },
        "variables": {}
    }
    if name is not None and value is not None:
        great_passage["variables"][name] = value
    return json.dumps(great_passage)


def call_f_api(id_token, step):
    """
        Passes an naIdToken to the f generation API (default: imink) &
        fetches the response (f token, UUID, and timestamp).
    """
    api_head = {
        'User-Agent': f's3s/{A_VERSION}',
        'Content-Type': 'application/json; charset=utf-8'
    }
    api_body = {
        'token': id_token,
        'hash_method': step
    }
    api_response = requests.post(F_GEN_URL, data=json.dumps(api_body), headers=api_head)
    resp = json.loads(api_response.text)

    f = resp["f"]
    uuid = resp["request_id"]
    timestamp = resp["timestamp"]
    return f, uuid, timestamp


def get_api_token(session_token):
    app_head = {
        'Host': 'accounts.nintendo.com',
        'Accept-Encoding': 'gzip',
        'Content-Type': 'application/json',
        'Content-Length': '436',
        'Accept': 'application/json',
        'Connection': 'Keep-Alive',
        'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 7.1.2)'
    }
    body = {
        'client_id': '71b963c1b7b6d119',
        'session_token': session_token,
        'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer-session-token'
    }
    url = "https://accounts.nintendo.com/connect/1.0.0/api/token"
    r = requests.post(url, headers=app_head, json=body)
    id_response = json.loads(r.text)
    return id_response


def get_user_info(id_response):
    app_head = {
        'User-Agent': 'NASDKAPI; Android',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {id_response["access_token"]}',
        'Host': 'api.accounts.nintendo.com',
        'Connection': 'Keep-Alive',
        'Accept-Encoding': 'gzip'
    }
    url = "https://api.accounts.nintendo.com/2.0.0/users/me"
    r = requests.get(url, headers=app_head)
    user_info = json.loads(r.text)
    return user_info


class NintendoApi:

    def __init__(self):
        self.config_data: dict = {}
        self.nso_app_version = None
        self.webview_version = None
        self.user_account_url = None
        self.auth_code_verifier = None
        self.init_config()

    def init_config(self):
        config_path_parent = TEXT_PATH / "nintendo"
        if not config_path_parent.exists():
            config_path_parent.mkdir(parents=True)
        config_path = config_path_parent / "config.json"
        # 打开配置文件, 如果不存在则创建默认配置写入
        if not config_path.exists():
            config_data = {"acc_loc": "", "g_token": "", "bullet_token": "", "session_token": ""}
            self.write_config(config_data)
        # 读取配置文件
        with open(config_path, "r") as f:
            self.config_data = json.load(f)
        # 初始化NSO版本
        self.init_nso_app_version()
        # 初始化WebView版本
        self.init_web_view_ver()
        # 初始化语言区域
        self.init_language(None)

    @staticmethod
    def write_config(config_data):
        config_path_parent = TEXT_PATH / "nintendo"
        if not config_path_parent.exists():
            config_path_parent.mkdir(parents=True)
        config_path = config_path_parent / "config.json"
        with open(config_path, "w") as f:
            f.write(json.dumps(config_data, indent=4, sort_keys=False, separators=(',', ': ')))

    def set_user_account_url(self, user_account_url):
        """Sets the user account URL."""
        self.user_account_url = user_account_url

    def init_language(self, language_code):
        """Prompts the user to set their game language."""
        if not language_code:
            self.config_data["acc_loc"] = ACC_LOCALE  # default
        else:
            self.config_data["acc_loc"] = language_code

    def init_web_view_ver(self):
        """Finds & parses the SplatNet 3 main.js file to fetch the current site version and sets it globally."""
        if self.webview_version:
            return self.webview_version
        else:
            home = get_nintendo_web_text()
            self.webview_version = get_nintendo_web_ver(home)
            return self.webview_version

    def init_nso_app_version(self):
        """Fetches the current Nintendo Switch Online app version from the Apple App Store and sets it globally."""
        if self.nso_app_version:
            return self.nso_app_version
        else:
            try:
                page = requests.get("https://apps.apple.com/us/app/nintendo-switch-online/id1234806557")
                soup = BeautifulSoup(page.text, 'html.parser')
                elt = soup.find("p", {"class": "whats-new__latest__version"})
                ver = elt.get_text().replace("Version ", "").strip()
                self.nso_app_version = ver
            except:
                self.nso_app_version = NSO_APP_VERSION

    def get_access_token(self, id_response, user_info, f, uuid, timestamp):
        body = {}
        id_token = id_response["id_token"]
        parameter = {
            'f': f,
            'language': user_info["language"],
            'naBirthday': user_info["birthday"],
            'naCountry': user_info["country"],
            'naIdToken': id_token,
            'requestId': uuid,
            'timestamp': timestamp
        }
        body["parameter"] = parameter
        app_head = {
            'X-Platform': 'Android',
            'X-ProductVersion': self.nso_app_version,
            'Content-Type': 'application/json; charset=utf-8',
            'Content-Length': str(990 + len(f)),
            'Connection': 'Keep-Alive',
            'Accept-Encoding': 'gzip',
            'User-Agent': f'com.nintendo.znca/{self.nso_app_version}(Android/7.1.2)',
        }
        url = "https://api-lp1.znc.srv.nintendo.net/v3/Account/Login"
        r = requests.post(url, headers=app_head, json=body)
        splatoon_token = json.loads(r.text)
        access_token = None
        try:
            access_token = splatoon_token["result"]["webApiServerCredential"]["accessToken"]
        except:
            # retry once if 9403/9599 error from nintendo
            try:
                f, uuid, timestamp = call_f_api(id_token, 1)
                body["parameter"]["f"] = f
                body["parameter"]["requestId"] = uuid
                body["parameter"]["timestamp"] = timestamp
                app_head["Content-Length"] = str(990 + len(f))
                url = "https://api-lp1.znc.srv.nintendo.net/v3/Account/Login"
                r = requests.post(url, headers=app_head, json=body)
                splatoon_token = json.loads(r.text)
                access_token = splatoon_token["result"]["webApiServerCredential"]["accessToken"]
            except:
                log.warning("Error from Nintendo (in Account/Login step):")
        return f, uuid, timestamp, access_token

    def get_web_service_token(self, id_token, f, uuid, timestamp):
        app_head = {
            'X-Platform': 'Android',
            'X-ProductVersion': self.nso_app_version,
            'Authorization': f'Bearer {id_token}',
            'Content-Type': 'application/json; charset=utf-8',
            'Content-Length': '391',
            'Accept-Encoding': 'gzip',
            'User-Agent': f'com.nintendo.znca/{self.nso_app_version}(Android/7.1.2)'
        }
        body = {}
        parameter = {
            'f': f,
            'id': 4834290508791808,
            'registrationToken': id_token,
            'requestId': uuid,
            'timestamp': timestamp
        }
        body["parameter"] = parameter

        url = "https://api-lp1.znc.srv.nintendo.net/v2/Game/GetWebServiceToken"
        r = requests.post(url, headers=app_head, json=body)
        web_service_resp = json.loads(r.text)
        web_service_token = None
        try:
            web_service_token = web_service_resp["result"]["webServiceToken"]
        except:
            # retry once if 9403/9599 error from nintendo
            try:
                f, uuid, timestamp = call_f_api(id_token, 2)
                body["parameter"]["f"] = f
                body["parameter"]["requestId"] = uuid
                body["parameter"]["timestamp"] = timestamp
                url = "https://api-lp1.znc.srv.nintendo.net/v2/Game/GetWebServiceToken"
                r = requests.post(url, headers=app_head, json=body)
                web_service_resp = json.loads(r.text)
                web_service_token = web_service_resp["result"]["accessToken"]
            except:
                log.warning("Failed to get web service token.")
        return web_service_token

    def link(self):
        """Logs in to a Nintendo Account and returns a session_token."""
        auth_state = base64.urlsafe_b64encode(os.urandom(36))
        auth_code_verifier = base64.urlsafe_b64encode(os.urandom(32))
        auth_cv_hash = hashlib.sha256()
        auth_cv_hash.update(auth_code_verifier.replace(b"=", b""))
        auth_code_challenge = base64.urlsafe_b64encode(auth_cv_hash.digest())
        body = {
            'state': auth_state,
            'redirect_uri': 'npf71b963c1b7b6d119://auth',
            'client_id': '71b963c1b7b6d119',
            'scope': 'openid user user.birthday user.mii user.screenName',
            'response_type': 'session_token_code',
            'session_token_code_challenge': auth_code_challenge.replace(b"=", b""),
            'session_token_code_challenge_method': 'S256',
            'theme': 'login_form'
        }
        link_msg = f'''https://accounts.nintendo.com/connect/1.0.0/authorize?{urllib.parse.urlencode(body)}
        右键单击 \"选择此人\" 按钮, 复制链接地址, 然后粘贴到这里.
        '''
        self.auth_code_verifier = auth_code_verifier
        return link_msg

    def log_in(self, use_account_url):
        """Logs in to a Nintendo Account and returns a session_token."""
        try:
            session_token_code = re.search('de=(.*)&', use_account_url)
            session_token = get_session_token(self.nso_app_version, session_token_code.group(1),
                                              self.auth_code_verifier)
            self.set_user_account_url(use_account_url)
            self.config_data["session_token"] = session_token
            return session_token
        except KeyboardInterrupt:
            log.debug("Bye!")
        except AttributeError:
            log.debug("Malformed URL. Please try again, or press Ctrl+C to exit.")
        except KeyError:  # session_token not found
            log.debug("\nThe URL has expired. Please log out and back into your Nintendo Account and try again.")

    def get_bullet(self, web_service_token, app_user_agent, user_lang, user_country):
        """Given a g_token, returns a bulletToken."""
        app_head = {
            'Content-Length': '0',
            'Content-Type': 'application/json',
            'Accept-Language': user_lang,
            'User-Agent': app_user_agent,
            'X-Web-View-Ver': self.webview_version,
            'X-NACOUNTRY': user_country,
            'Accept': '*/*',
            'Origin': SPLATNET3_URL,
            'X-Requested-With': 'com.nintendo.znca'
        }
        app_cookies = {
            '_gtoken': web_service_token,  # X-GameWebToken
            '_dnt': '1'  # Do Not Track
        }
        url = SPLATNET3_URL + BULLET_PATH
        r = requests.post(url, headers=app_head, cookies=app_cookies)

        if r.status_code == 401:
            log.error("Unauthorized error (ERROR_INVALID_GAME_WEB_TOKEN). Cannot fetch tokens at this time.")
        elif r.status_code == 403:
            log.error("Forbidden error (ERROR_OBSOLETE_VERSION). Cannot fetch tokens at this time.")
        elif r.status_code == 204:  # No Content, USER_NOT_REGISTERED
            log.error("Cannot access SplatNet 3 without having played online.")

        bullet_resp = json.loads(r.text)
        bullet_token = bullet_resp["bulletToken"]
        return bullet_token

    def get_g_token(self, session_token):
        """Provided the session_token, returns a GameWebToken JWT and account info."""
        id_response = get_api_token(session_token)
        # get user info
        user_info = get_user_info(id_response)
        user_nickname = user_info["nickname"]
        user_lang = user_info["language"]
        user_country = user_info["country"]

        f, uuid, timestamp = call_f_api(id_response["id_token"], 1)
        # get splatoon access token
        f, uuid, timestamp, id_token = self.get_access_token(id_response, user_info, f, uuid, timestamp)
        # get web service token
        web_service_token = self.get_web_service_token(id_token, f, uuid, timestamp)
        return web_service_token, user_nickname, user_lang, user_country

    def gen_new_tokens(self, reason, force=False):
        """Attempts to generate new tokens when the saved ones have expired."""
        if not self.config_data["session_token"] or reason == "expiry":
            log.info("Please log in to your Nintendo Account to obtain your session_token.")
            new_token = self.log_in(self.user_account_url)
            if not new_token:
                log.error("There was a problem logging you in. Please try again later.")
            else:
                log.info("Wrote session_token to config.txt.")
            self.config_data["session_token"] = new_token
        log.debug("Attempting to generate new g_token and bulletToken...")

        new_g_token, acc_name, acc_lang, acc_country = self.get_g_token(self.config_data["session_token"])
        new_bullet_token = self.get_bullet(new_g_token, DEFAULT_USER_AGENT, acc_lang, acc_country)

        self.config_data["g_token"] = new_g_token  # valid for 6 hours
        self.config_data["bullet_token"] = new_bullet_token  # valid for 2 hours
        self.config_data["acc_loc"] = f"{acc_lang}|{acc_country}"
        self.write_config(self.config_data)

        if not new_bullet_token:
            log.error("Wrote g_token to config.txt, but could not generate bulletToken.")
        else:
            log.info(f"Wrote tokens for {acc_name} to config.txt.\n")

    def prefetch_checks(self):
        """
            Queries the SplatNet 3 homepage to check if our g_token & bulletToken are still valid
            and regenerates them if not.
        """
        log.debug("Validating your tokens...")
        if any([not self.config_data["session_token"], not self.config_data["g_token"],
                not self.config_data["bullet_token"]]):
            self.gen_new_tokens("blank")
        sha = TRANSLATE_RID["HomeQuery"]
        test = requests.post(SPLATNET3_URL + GRAPHQL_PATH,
                             data=gen_graphql_body(sha),
                             headers=self.gen_head(),
                             cookies=dict(_gtoken=self.config_data["g_token"]))
        if test.status_code != 200:
            self.gen_new_tokens("expiry")
        else:
            log.debug("Validating your tokens... done.\n")

    def bind(self, user_account_url):
        self.log_in(user_account_url)
        self.prefetch_checks()
        log.debug("* prefetch_checks() succeeded")
        log.debug("* binding to SplatNet 3...")
        # TODO bind

    def get_ranked_battle_records(self):
        """Returns a list of ranked battle records."""
        # TODO
        parents, results, coop_results = self.fetch_json(export_all=True)
        return parents

    def fetch_json(self, separate=False, export_all=False, skip_prefetch=False):
        """Returns results JSON from SplatNet 3, including a combined dictionary for battles + SR jobs if requested."""
        if not skip_prefetch:
            self.prefetch_checks()
            log.debug("* prefetch_checks() succeeded")
        else:
            log.debug("* skipping prefetch_checks()")

        ink_list, salmon_list = [], []
        parent_files = []

        queries = ["RegularBattleHistoriesQuery", "BankaraBattleHistoriesQuery", "XBattleHistoriesQuery",
                   "PrivateBattleHistoriesQuery", "LatestBattleHistoriesQuery", "CoopHistoryQuery"]

        for sha in queries:
            log.debug(f"* making query1 to {sha}")
            lang = 'en-US' if sha == "CoopHistoryQuery" else None
            sha = TRANSLATE_RID[sha]
            battle_ids, job_ids = [], []

            query1 = requests.post(SPLATNET3_URL + GRAPHQL_PATH,
                                   data=gen_graphql_body(sha),
                                   headers=self.gen_head(force_lang=lang),
                                   cookies=dict(_gtoken=self.config_data["g_token"]))
            query1_resp = json.loads(query1.text)
            # ink battles - latest 50 of any type
            if "latestBattleHistories" in query1_resp["data"]:
                for battle_group in query1_resp["data"]["latestBattleHistories"]["historyGroups"]["nodes"]:
                    for battle in battle_group["historyDetails"]["nodes"]:
                        battle_ids.append(
                            battle["id"])  # don't filter out private battles here - do that in post_result()
            # ink battles - latest 50 turf war
            elif "regularBattleHistories" in query1_resp["data"]:
                needs_sorted = True
                for battle_group in query1_resp["data"]["regularBattleHistories"]["historyGroups"]["nodes"]:
                    for battle in battle_group["historyDetails"]["nodes"]:
                        battle_ids.append(battle["id"])
            # ink battles - latest 50 anarchy battles
            elif "bankaraBattleHistories" in query1_resp["data"]:
                needs_sorted = True
                for battle_group in query1_resp["data"]["bankaraBattleHistories"]["historyGroups"]["nodes"]:
                    for battle in battle_group["historyDetails"]["nodes"]:
                        battle_ids.append(battle["id"])
            # ink battles - latest 50 x battles
            elif "xBattleHistories" in query1_resp["data"]:
                needs_sorted = True
                for battle_group in query1_resp["data"]["xBattleHistories"]["historyGroups"]["nodes"]:
                    for battle in battle_group["historyDetails"]["nodes"]:
                        battle_ids.append(battle["id"])
            # ink battles - latest 50 private battles
            elif "privateBattleHistories" in query1_resp["data"] \
                    and not self.custom_key_exists("ignore_private", self.config_data):
                needs_sorted = True
                for battle_group in query1_resp["data"]["privateBattleHistories"]["historyGroups"]["nodes"]:
                    for battle in battle_group["historyDetails"]["nodes"]:
                        battle_ids.append(battle["id"])

            # salmon run jobs - latest 50
            elif "coopResult" in query1_resp["data"]:
                for shift in query1_resp["data"]["coopResult"]["historyGroups"]["nodes"]:
                    for job in shift["historyDetails"]["nodes"]:
                        job_ids.append(job["id"])
            parent_files.append(query1_resp)

        if export_all:
            return parent_files, ink_list, salmon_list
        else:
            if separate:
                return ink_list, salmon_list
            else:
                combined = ink_list + salmon_list
                return combined

    def gen_head(self, force_lang=None):
        """Returns a (dynamic!) header used for GraphQL requests."""
        if force_lang:
            lang = force_lang
            country = force_lang[-2:]
        else:
            lang = self.config_data["acc_loc"][:5]
            country = self.config_data["acc_loc"][-2:]

        graphql_head = {
            'Authorization': f'Bearer {self.config_data["bullet_token"]}',
            # update every time it's called with current global var
            'Accept-Language': lang,
            'User-Agent': DEFAULT_USER_AGENT,
            'X-Web-View-Ver': self.webview_version,
            'Content-Type': 'application/json',
            'Accept': '*/*',
            'Origin': SPLATNET3_URL,
            'X-Requested-With': 'com.nintendo.znca',
            'Referer': f'{SPLATNET3_URL}?lang={lang}&na_country={country}&na_lang={lang}',
            'Accept-Encoding': 'gzip, deflate'
        }
        return graphql_head

    @staticmethod
    def translate_gear_ability(url):
        """Given a URL, returns the gear ability string corresponding to the filename hash."""

        hash_map = {
            '5c98cc37d2ce56291a7e430459dc9c44d53ca98b8426c5192f4a53e6dd6e4293': 'ink_saver_main',
            '11293d8fe7cfb82d55629c058a447f67968fc449fd52e7dd53f7f162fa4672e3': 'ink_saver_sub',
            '29b845ea895b931bfaf895e0161aeb47166cbf05f94f04601769c885d019073b': 'ink_recovery_up',
            '3b6c56c57a6d8024f9c7d6e259ffa2e2be4bdf958653b834e524ffcbf1e6808e': 'run_speed_up',
            '087ffffe40c28a40a39dc4a577c235f4cc375540c79dfa8ede1d8b63a063f261': 'swim_speed_up',
            'e8668a2af7259be74814a9e453528a3e9773435a34177617a45bbf79ad0feb17': 'special_charge_up',
            'e3154ab67494df2793b72eabf912104c21fbca71e540230597222e766756b3e4': 'special_saver',
            'fba267bd56f536253a6bcce1e919d8a48c2b793c1b554ac968af8d2068b22cab': 'special_power_up',
            'aaa9b7e95a61bfd869aaa9beb836c74f9b8d4e5d4186768a27d6e443c64f33ce': 'quick_respawn',
            '138820ed46d68bdf2d7a21fb3f74621d8fc8c2a7cb6abe8d7c1a3d7c465108a7': 'quick_super_jump',
            '9df9825e470e00727aa1009c4418cf0ace58e1e529dab9a7c1787309bb25f327': 'sub_power_up',
            'db36f7e89194ed642f53465abfa449669031a66d7538135c703d3f7d41f99c0d': 'ink_resistance_up',
            '664489b24e668ef1937bfc9a80a8cf9cf4927b1e16481fa48e7faee42122996d': 'sub_resistance_up',
            '1a0c78a1714c5abababd7ffcba258c723fefade1f92684aa5f0ff7784cc467d0': 'intensify_action',
            '85d97cd3d5890b80e020a554167e69b5acfa86e96d6e075b5776e6a8562d3d4a': 'opening_gambit',
            'd514787f65831c5121f68b8d96338412a0d261e39e522638488b24895e97eb88': 'last_ditch_effort',
            'aa5b599075c3c1d27eff696aeded9f1e1ddf7ae3d720268e520b260db5600d60': 'tenacity',
            '748c101d23261aee8404c573a947ffc7e116a8da588c7371c40c4f2af6a05a19': 'comeback',
            '2c0ef71abfb3efe0e67ab981fc9cd46efddcaf93e6e20da96980079f8509d05d': 'ninja_squid',
            'de15cad48e5f23d147449c70ee4e2973118959a1a115401561e90fc65b53311b': 'haunt',
            '56816a7181e663b5fedce6315eb0ad538e0aadc257b46a630fcfcc4a16155941': 'thermal_ink',
            'de0d92f7dfed6c76772653d6858e7b67dd1c83be31bd2324c7939105180f5b71': 'respawn_punisher',
            '0d6607b6334e1e84279e482c1b54659e31d30486ef0576156ee0974d8d569dbc': 'ability_doubler',
            'f9c21eacf6dbc1d06edbe498962f8ed766ab43cb1d63806f3731bf57411ae7b6': 'stealth_jump',
            '9d982dc1a7a8a427d74df0edcebcc13383c325c96e75af17b9cdb6f4e8dafb24': 'object_shredder',
            '18f03a68ee64da0a2e4e40d6fc19de2e9af3569bb6762551037fd22cf07b7d2d': 'drop_roller',
            'dc937b59892604f5a86ac96936cd7ff09e25f18ae6b758e8014a24c7fa039e91': None
        }

        for entry in hash_map:
            if entry in url:
                return hash_map[entry]

    @staticmethod
    def set_noun(which):
        """Returns the term to be used when referring to the type of results in question."""

        if which == "both":
            return "battles/jobs"
        elif which == "salmon":
            return "jobs"
        else:  # "ink"
            return "battles"

    @staticmethod
    def convert_color(rgbadict):
        '''Given a dict of numbers from 0.0 - 1.0, converts these into a RGBA hex color format (without the leading
        #). '''

        r = int(255 * rgbadict["r"])
        g = int(255 * rgbadict["g"])
        b = int(255 * rgbadict["b"])
        a = int(255 * rgbadict["a"])
        return f"{r:02x}{g:02x}{b:02x}{a:02x}"

    @staticmethod
    def convert_tricolor_role(string):
        """Given a SplatNet 3 Tricolor Turf War team role, convert it to the stat.ink string format."""

        if string == "DEFENSE":
            return "defender"
        else:  # ATTACK1 or ATTACK2
            return "attacker"

    @staticmethod
    def b64d(string):
        """Base64-decodes a string and cuts off the SplatNet prefix."""

        thing_id = base64.b64decode(string).decode('utf-8')
        thing_id = thing_id.replace("VsStage-", "")
        thing_id = thing_id.replace("VsMode-", "")
        thing_id = thing_id.replace("CoopStage-", "")
        thing_id = thing_id.replace("CoopGrade-", "")
        thing_id = thing_id.replace("CoopEnemy-", "")
        thing_id = thing_id.replace("CoopEventWave-", "")
        thing_id = thing_id.replace("CoopUniform-", "")
        thing_id = thing_id.replace("SpecialWeapon-", "")

        if "Weapon-" in thing_id:
            thing_id = thing_id.replace("Weapon-", "")
            if len(thing_id) == 5 and thing_id[:1] == "2" and thing_id[-3:] == "900":  # grizzco weapon ID from a hacker
                return ""

        if thing_id[:15] == "VsHistoryDetail" or thing_id[:17] == "CoopHistoryDetail" or thing_id[:8] == "VsPlayer":
            return thing_id  # string
        else:
            return int(thing_id)  # integer

    @staticmethod
    def epoch_time(time_string):
        """Converts a playedTime string into an integer representing the epoch time."""

        utc_time = datetime.datetime.strptime(time_string, "%Y-%m-%dT%H:%M:%SZ")
        epoch_time = int((utc_time - datetime.datetime(1970, 1, 1)).total_seconds())
        return epoch_time

    @staticmethod
    def custom_key_exists(key, config_data, value=True):
        """Checks if a given custom key exists in config.txt and is set to the specified value (true by default)."""

        # https://github.com/frozenpandaman/s3s/wiki/config-keys
        if key not in SUPPORTED_KEYS:
            log.warning("(!) Checking unexpected custom key")
        return str(config_data.get(key, None)).lower() == str(value).lower()

    def main(self):
        self.init_language(None)
        self.prefetch_checks()
        print("Fetching your JSON files to export locally. This might take a while...")
        parents, results, coop_results = self.fetch_json(separate=True, export_all=True, skip_prefetch=True)

        cwd = os.getcwd()
        export_dir = os.path.join(cwd, f'export-{int(time.time())}')
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)

        if parents is not None:
            with open(os.path.join(cwd, export_dir, "overview.json"), "x") as fout:
                json.dump(parents, fout)
                log.debug("Created overview.json with general info about your battle and job stats.")

        if results is not None:
            with open(os.path.join(cwd, export_dir, "results.json"), "x") as fout:
                json.dump(results, fout)
                log.debug("Created results.json with detailed recent battle stats (up to 50 of each type).")

        if coop_results is not None:
            with open(os.path.join(cwd, export_dir, "coop_results.json"), "x") as fout:
                json.dump(coop_results, fout)
                log.debug("Created coop_results.json with detailed recent Salmon Run job stats (up to 50).")

        log.info("Have fun playing Splatoon 3! :) Bye!")

        thread_pool.shutdown(wait=True)


if __name__ == '__main__':
    nin = NintendoApi()
    nin.main()
