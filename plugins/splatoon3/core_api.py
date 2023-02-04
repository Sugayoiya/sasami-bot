import json
import os
import re
import sys
import time

import requests
from bs4 import BeautifulSoup

from utils import nintendo

# CONFIG.TXT CREATION
if getattr(sys, 'frozen', False):  # place config.txt in same directory as script (bundled or not)
    app_path = os.path.dirname(sys.executable)
elif __file__:
    app_path = os.path.dirname(__file__)
config_path = os.path.join(app_path, "config.txt")

try:
    config_file = open(config_path, "r")
    CONFIG_DATA = json.load(config_file)
    config_file.close()
except (IOError, ValueError):
    print("Generating new config file.")
    CONFIG_DATA = {"api_key": "", "acc_loc": "", "gtoken": "", "bullettoken": "", "session_token": "",
                   "f_gen": "https://api.imink.app/f"}
    config_file = open(config_path, "w")
    config_file.seek(0)
    config_file.write(json.dumps(CONFIG_DATA, indent=4, sort_keys=False, separators=(',', ': ')))
    config_file.close()
    config_file = open(config_path, "r")
    CONFIG_DATA = json.load(config_file)
    config_file.close()

# SET GLOBALS
API_KEY = CONFIG_DATA["api_key"]  # for stat.ink
USER_LANG = CONFIG_DATA["acc_loc"][:5]  # nintendo account info
USER_COUNTRY = CONFIG_DATA["acc_loc"][-2:]  # nintendo account info
G_TOKEN = CONFIG_DATA["gtoken"]  # for accessing splatnet - base64
BULLET_TOKEN = CONFIG_DATA["bullettoken"]  # for accessing splatnet - base64 JWT
SESSION_TOKEN = CONFIG_DATA["session_token"]  # for nintendo login
F_GEN_URL = CONFIG_DATA["f_gen"]  # endpoint for generating f (imink API by default)

SPLATNET3_URL = "https://api.lp1.av5ja.srv.nintendo.net"
GRAPHQL_URL = "https://api.lp1.av5ja.srv.nintendo.net/api/graphql"
WEB_VIEW_VERSION = "1.0.0-d3a90678"

# SET HTTP HEADERS
if "app_user_agent" in CONFIG_DATA:
    APP_USER_AGENT = str(CONFIG_DATA["app_user_agent"])
else:
    APP_USER_AGENT = 'Mozilla/5.0 (Linux; Android 11; Pixel 5) ' \
                     'AppleWebKit/537.36 (KHTML, like Gecko) ' \
                     'Chrome/94.0.4606.61 Mobile Safari/537.36'

# SHA256 hash database for SplatNet 3 GraphQL queries
# full list: https://github.com/samuelthomas2774/nxapi/discussions/11#discussioncomment-3614603
translate_rid = {
    'HomeQuery': 'dba47124d5ec3090c97ba17db5d2f4b3',  # blank vars
    'LatestBattleHistoriesQuery': '7d8b560e31617e981cf7c8aa1ca13a00',  # INK / blank vars - query1
    'RegularBattleHistoriesQuery': '819b680b0c7962b6f7dc2a777cd8c5e4',  # INK / blank vars - query1
    'BankaraBattleHistoriesQuery': 'c1553ac75de0a3ea497cdbafaa93e95b',  # INK / blank vars - query1
    'PrivateBattleHistoriesQuery': '51981299595060692440e0ca66c475a1',  # INK / blank vars - query1
    'VsHistoryDetailQuery': 'cd82f2ade8aca7687947c5f3210805a6',  # INK / req "vsResultId" - query2
    'CoopHistoryQuery': '817618ce39bcf5570f52a97d73301b30',  # SR  / blank vars - query1
    'CoopHistoryDetailQuery': 'f3799a033f0a7ad4b1b396f9a3bafb1e',  # SR  / req "coopHistoryDetailId" - query2
    'ScheduleData': '10e1d424391e78d21670227550b3509f',
    'GesotownData': 'd08dbdd29f31471e61daa978feea697a',
}


def get_web_view_ver():
    '''Find & parse the SplatNet 3 main.js file for the current site version.'''

    splatnet3_home = requests.get(SPLATNET3_URL)
    soup = BeautifulSoup(splatnet3_home.text, "html.parser")

    main_js = soup.select_one("script[src*='static']")
    if not main_js:
        return WEB_VIEW_VERSION

    main_js_url = SPLATNET3_URL + main_js.attrs["src"]
    main_js_body = requests.get(main_js_url)

    match = re.search(r"\b(\d+\.\d+\.\d+)\b-\".concat.*?\b([0-9a-f]{40})\b", main_js_body.text)
    if not match:
        return WEB_VIEW_VERSION

    version, revision = match.groups()
    return f"{version}-{revision[:8]}"


def write_config(tokens):
    '''Writes config file and updates the global variables.'''

    config_file = open(config_path, "w")
    config_file.seek(0)
    config_file.write(json.dumps(tokens, indent=4, sort_keys=False, separators=(',', ': ')))
    config_file.close()

    config_file = open(config_path, "r")
    CONFIG_DATA = json.load(config_file)

    global API_KEY
    API_KEY = CONFIG_DATA["api_key"]
    global USER_LANG
    USER_LANG = CONFIG_DATA["acc_loc"][:5]
    global USER_COUNTRY
    USER_COUNTRY = CONFIG_DATA["acc_loc"][-2:]
    global G_TOKEN
    G_TOKEN = CONFIG_DATA["gtoken"]
    global BULLET_TOKEN
    BULLET_TOKEN = CONFIG_DATA["bullettoken"]
    global SESSION_TOKEN
    SESSION_TOKEN = CONFIG_DATA["session_token"]

    config_file.close()


def headbutt():
    '''Return a (dynamic!) header used for GraphQL requests.'''

    graphql_head = {
        'Authorization': f'Bearer {BULLET_TOKEN}',  # update every time it's called with current global var
        'Accept-Language': USER_LANG,
        'User-Agent': APP_USER_AGENT,
        'X-Web-View-Ver': get_web_view_ver(),
        'Content-Type': 'application/json',
        'Accept': '*/*',
        'Origin': 'https://api.lp1.av5ja.srv.nintendo.net',
        'X-Requested-With': 'com.nintendo.znca',
        'Referer': f'https://api.lp1.av5ja.srv.nintendo.net/?lang={USER_LANG}&na_country={USER_COUNTRY}&na_lang={USER_LANG}',
        'Accept-Encoding': 'gzip, deflate'
    }
    return graphql_head


def gen_graphql_body(sha256hash, varname=None, varvalue=None):
    '''Generates a JSON dictionary, specifying information to retrieve, to send with GraphQL requests.'''
    great_passage = {
        "extensions": {
            "persistedQuery": {
                "sha256Hash": sha256hash,
                "version": 1
            }
        },
        "variables": {}
    }

    if varname != None and varvalue != None:
        great_passage["variables"][varname] = varvalue

    return json.dumps(great_passage)


def main():
    if True:
        prefetch_checks()
        print("\nFetching your JSON files to export locally... this might take a while.")
        try:
            # fetch_json() calls prefetch_checks() to gen or check tokens
            parents, results, coop_results = fetch_json("both", separate=True, exportall=True, specific=True)
        except Exception as e:
            print("Ran into an error:")
            print(e)
            print("Please run the script again.")
            sys.exit(1)

        print("Exporting results to local files...")

        cwd = os.getcwd()
        export_dir = os.path.join(cwd, f'export-{int(time.time())}')
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)

        if parents != None:
            with open(os.path.join(cwd, export_dir, "overview.json"), "x") as fout:
                json.dump(parents, fout)
                print("Created overview.json with general info about your battle and job stats.")

        if results != None:
            with open(os.path.join(cwd, export_dir, "results.json"), "x") as fout:
                json.dump(results, fout)
                print("Created results.json with detailed recent battle stats (up to 50 of each type).")

        if coop_results != None:
            with open(os.path.join(cwd, export_dir, "coop_results.json"), "x") as fout:
                json.dump(coop_results, fout)
                print("Created coop_results.json with detailed recent Salmon Run job stats (up to 50).")

        print("\nHave fun playing Splatoon 3! :) Bye!")
        sys.exit(0)


def prefetch_checks():
    '''Queries the SplatNet 3 homepage to check if our gtoken cookie and bulletToken are still valid, otherwise regenerate.'''

    if SESSION_TOKEN == "" or G_TOKEN == "" or BULLET_TOKEN == "":
        gen_new_tokens("blank")

    sha = translate_rid["HomeQuery"]
    test = requests.post(GRAPHQL_URL, data=gen_graphql_body(sha), headers=headbutt(), cookies=dict(_gtoken=G_TOKEN))
    if test.status_code != 200:
        gen_new_tokens("expiry")


def gen_new_tokens(reason, force=False):
    '''Attempts to generate new tokens when the saved ones have expired.'''

    manual_entry = False
    if force != True:  # unless we force our way through
        if reason == "blank":
            print("Blank token(s).")
        elif reason == "expiry":
            print("The stored tokens have expired.")
        else:
            print("Cannot access SplatNet 3 without having played online.")
            sys.exit(1)

    if SESSION_TOKEN == "":
        print("Please log in to your Nintendo Account to obtain your session_token.")
        new_token = nintendo.log_in()
        if new_token == None:
            print("There was a problem logging you in. Please try again later.")
        elif new_token == "skip":
            manual_entry = True
        else:
            print("\nWrote session_token to config.txt.")
        CONFIG_DATA["session_token"] = new_token
        write_config(CONFIG_DATA)
    elif SESSION_TOKEN == "skip":
        manual_entry = True

    print("Attempting to generate new gtoken and bulletToken...")
    new_gtoken, acc_name, acc_lang, acc_country = nintendo.get_gtoken(F_GEN_URL, SESSION_TOKEN)
    new_bullettoken = nintendo.get_bullet(new_gtoken, get_web_view_ver(), APP_USER_AGENT, acc_lang, acc_country)
    CONFIG_DATA["gtoken"] = new_gtoken  # valid for 2 hours
    CONFIG_DATA["bullettoken"] = new_bullettoken  # valid for 2 hours
    CONFIG_DATA["acc_loc"] = acc_lang + "|" + acc_country
    write_config(CONFIG_DATA)

    if manual_entry:
        print("Wrote tokens to config.txt.")
    else:
        print(f"Wrote tokens for {acc_name} to config.txt.")


def fetch_json(which, separate=False, exportall=False, specific=False):
    '''Returns results JSON from SplatNet 3, including a combined dict for ink battles + SR jobs if requested.'''

    if exportall and not separate:
        print("fetch_json() must be called with separate=True if using exportall.")
        sys.exit(1)

    prefetch_checks()

    ink_list, salmon_list = [], []
    parent_files = []

    sha_list = []
    # sha_list.append(translate_rid["RegularBattleHistoriesQuery"])
    # sha_list.append(translate_rid["BankaraBattleHistoriesQuery"])
    # sha_list.append(translate_rid["PrivateBattleHistoriesQuery"])
    # sha_list.append(translate_rid["LatestBattleHistoriesQuery"])
    # sha_list.append(translate_rid["CoopHistoryQuery"])

    sha_list.append(translate_rid["ScheduleData"])
    sha_list.append(translate_rid["GesotownData"])

    for sha in sha_list:
        if sha is not None:
            battle_ids, job_ids = [], []

            query1 = requests.post(GRAPHQL_URL, data=gen_graphql_body(sha), headers=headbutt(),
                                   cookies=dict(_gtoken=G_TOKEN))
            query1_resp = json.loads(query1.text)

            # print(json.dumps(query1_resp, indent=4, sort_keys=True))

            # ink battles - latest 50 of any type
            if "latestBattleHistories" in query1_resp["data"]:
                for battle_group in query1_resp["data"]["latestBattleHistories"]["historyGroups"]["nodes"]:
                    for battle in battle_group["historyDetails"]["nodes"]:
                        battle_ids.append(battle["id"])
            # ink battles - latest 50 turf war
            elif "regularBattleHistories" in query1_resp["data"]:
                for battle_group in query1_resp["data"]["regularBattleHistories"]["historyGroups"]["nodes"]:
                    for battle in battle_group["historyDetails"]["nodes"]:
                        battle_ids.append(battle["id"])
            # ink battles - latest 50 ranked battles
            elif "bankaraBattleHistories" in query1_resp["data"]:
                for battle_group in query1_resp["data"]["bankaraBattleHistories"]["historyGroups"]["nodes"]:
                    for battle in battle_group["historyDetails"]["nodes"]:
                        battle_ids.append(battle["id"])
            # ink battles - latest 50 private battles
            elif "privateBattleHistories" in query1_resp["data"]:
                for battle_group in query1_resp["data"]["privateBattleHistories"]["historyGroups"]["nodes"]:
                    for battle in battle_group["historyDetails"]["nodes"]:
                        battle_ids.append(battle["id"])
            # salmon run jobs - latest 50
            elif "coopResult" in query1_resp["data"]:
                for shift in query1_resp["data"]["coopResult"]["historyGroups"]["nodes"]:
                    for job in shift["historyDetails"]["nodes"]:
                        job_ids.append(job["id"])

            for bid in battle_ids:
                query2_b = requests.post(GRAPHQL_URL,
                                         data=gen_graphql_body(translate_rid["VsHistoryDetailQuery"], "vsResultId",
                                                               bid),
                                         headers=headbutt(),
                                         cookies=dict(_gtoken=G_TOKEN))
                query2_resp_b = json.loads(query2_b.text)
                ink_list.append(query2_resp_b)

            for jid in job_ids:
                query2_j = requests.post(GRAPHQL_URL,
                                         data=gen_graphql_body(translate_rid["CoopHistoryDetailQuery"],
                                                               "coopHistoryDetailId", jid),
                                         headers=headbutt(),
                                         cookies=dict(_gtoken=G_TOKEN))
                query2_resp_j = json.loads(query2_j.text)
                salmon_list.append(query2_resp_j)

            parent_files.append(query1_resp)
        else:  # sha = None (we don't want to get the specified result type)
            pass

    if exportall:
        return parent_files, ink_list, salmon_list
    elif separate:
        return ink_list, salmon_list
    else:
        return ink_list + salmon_list
