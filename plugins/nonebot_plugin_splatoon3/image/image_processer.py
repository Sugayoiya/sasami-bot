from .image_processer_tools import *
from ..data import get_festivals_data
from ..utils import *

http = urllib3.PoolManager()


# 绘制 祭典地图
def get_festival(festivals):
    image_background_size = (1000, 670)
    group_img_size = (1000, 390)
    # 取背景rgb颜色
    bg_rgb = dict_bg_rgb["祭典"]
    # 创建纯色背景
    image_background = Image.new("RGBA", image_background_size, bg_rgb)
    bg_mask = get_file("festival_mask").resize((600, 400))
    # 填充小图蒙版
    image_background = tiled_fill(image_background, bg_mask)
    # 圆角化
    image_background = circle_corner(image_background, radii=16)

    festival = festivals[0]
    # 获取翻译
    _id = festival["__splatoon3ink_id"]
    trans_cht_festival_data = get_trans_cht_data()["festivals"][_id]
    # 替换为翻译
    teams_list = []
    festival["title"] = trans_cht_festival_data["title"]
    for v in range(3):
        festival["teams"][v]["teamName"] = trans_cht_festival_data["teams"][v]["teamName"]
        teams_list.append(festival["teams"][v])
    # 整理数据
    title = festival["title"]
    st = festival["startTime"]
    et = festival["endTime"]
    time_text = "{} {}  {} - {} {}  {}".format(
        time_converter_yd(st),
        "周" + dict_weekday_trans.get(time_converter_weekday(st)),
        time_converter_hm(st),
        time_converter_yd(et),
        "周" + dict_weekday_trans.get(time_converter_weekday(et)),
        time_converter_hm(et),
    )
    # 绘制标题
    font_size = 30
    text_bg = get_translucent_name_bg(title, 80, font_size)
    text_bg_size = text_bg.size
    # 贴上文字背景
    text_bg_pos = ((image_background_size[0] - text_bg_size[0]) // 2, 20)
    paste_with_a(image_background, text_bg, text_bg_pos)
    # 绘制阵营图片
    group_img = get_save_file(ImageInfo(title, festival["image"]["url"], title, "祭典阵营图片")).resize(group_img_size)
    group_img_pos = (0, text_bg_pos[1] + text_bg_size[1] + 20)
    paste_with_a(image_background, group_img, group_img_pos)
    # 绘制阵营名称
    drawer = ImageDraw.Draw(image_background)
    pos_w = group_img_size[0] // 6
    font_size = 24
    ttf = ImageFont.truetype(ttf_path_chinese, font_size)
    rectangle_h = 100
    for k, v in enumerate(teams_list):
        group_text_bg_rgb = (int(v["color"]["r"] * 100), int(v["color"]["g"] * 100), int(v["color"]["b"] * 100))
        # 绘制色块对比图
        satrt_xy = (0 + group_img_size[0] // 3 * k, group_img_pos[1] + group_img_size[1])
        end_xy = (satrt_xy[0] + group_img_size[0] // 3, satrt_xy[1] + rectangle_h)
        drawer.rectangle((satrt_xy, end_xy), fill=group_text_bg_rgb)
        # 绘制阵营名称
        group_text_bg = get_translucent_name_bg(v["teamName"], 100, font_size, group_text_bg_rgb)
        w, h = group_text_bg.size
        group_text_bg_pos = (pos_w - (w // 2), group_img_pos[1] + group_img_size[1] - h - 5)
        paste_with_a(image_background, group_text_bg, group_text_bg_pos)
        # 计算下一个
        pos_w += group_img_size[0] // 3
    # 绘制时间
    w, h = ttf.getsize(time_text)
    # 文字居中绘制
    time_text_pos = ((image_background_size[0] - w) / 2, group_img_pos[1] + group_img_size[1] + rectangle_h + 20)
    text_rgb = dict_bg_rgb["祭典时间-金黄"]
    drawer.text(time_text_pos, time_text, font=ttf, fill=text_rgb)

    return image_background


# 绘制 活动地图
def get_events(events):
    background_size = (1084, 1100 * len(events))
    event_card_bg_size = (background_size[0] - 40, 640)
    # 取背景rgb颜色
    bg_rgb = dict_bg_rgb["活动"]
    # 创建纯色背景
    image_background = Image.new("RGBA", background_size, bg_rgb)
    bg_mask = get_file("cat_paw_mask").resize((400, 250))
    # 填充小图蒙版
    image_background = tiled_fill(image_background, bg_mask)
    # 圆角
    image_background = circle_corner(image_background, radii=20)
    # 遍历每个活动
    pos_h = 0
    for index, event in enumerate(events):
        # 获取翻译
        cht_event_data = event["leagueMatchSetting"]["leagueMatchEvent"]
        _id = cht_event_data["id"]
        trans_cht_event_data = get_trans_cht_data()["events"][_id]
        # 替换为翻译文本
        cht_event_data["name"] = trans_cht_event_data["name"]
        cht_event_data["desc"] = trans_cht_event_data["desc"]
        cht_event_data["regulation"] = trans_cht_event_data["regulation"]

        # 顶部活动标志(大号)
        pos_h += 20
        game_mode_img_size = (80, 80)
        game_mode_img = get_file("event_bg").resize(game_mode_img_size, Image.ANTIALIAS)
        game_mode_img_pos = (20, pos_h)
        paste_with_a(image_background, game_mode_img, game_mode_img_pos)
        pos_h += game_mode_img_size[1] + 20
        # 绘制主标题
        main_title = cht_event_data["name"]
        drawer = ImageDraw.Draw(image_background)
        ttf = ImageFont.truetype(ttf_path_chinese, 40)
        main_title_pos = (game_mode_img_pos[0] + game_mode_img_size[0] + 20, game_mode_img_pos[1])
        main_title_size = ttf.getsize(main_title)
        drawer.text(main_title_pos, main_title, font=ttf, fill=(255, 255, 255))
        # 绘制描述
        desc = cht_event_data["desc"]
        ttf = ImageFont.truetype(ttf_path_chinese, 30)
        desc_pos = (main_title_pos[0], main_title_pos[1] + main_title_size[1] + 10)
        drawer.text(desc_pos, desc, font=ttf, fill=(255, 255, 255))
        # 绘制对战卡片
        event_card = get_event_card(event, event_card_bg_size)
        event_card_pos = (20, pos_h)
        paste_with_a(image_background, event_card, event_card_pos)
        pos_h += event_card_bg_size[1] + 10
        # 绘制祭典说明卡片
        event_desc_card_bg_size = (event_card_bg_size[0], 300)
        event_desc_card = get_event_desc_card(cht_event_data, event_desc_card_bg_size)
        event_card_pos = (20, pos_h)
        paste_with_a(image_background, event_desc_card, event_card_pos)
        pos_h += event_desc_card_bg_size[1]
        # 计算下一行高度
        pos_h += 20
    return image_background


# 绘制 竞赛地图
def get_stages(schedule, num_list, contest_match=None, rule_match=None):
    # 涂地
    regular = schedule["regularSchedules"]["nodes"]
    # 真格
    ranked = schedule["bankaraSchedules"]["nodes"]
    # X段
    xschedule = schedule["xSchedules"]["nodes"]
    # 祭典
    festivals = schedule["festSchedules"]["nodes"]

    # 如果存在祭典，且当前时间位于祭典，转变为输出祭典地图，后续不再进行处理
    if have_festival(festivals) and now_is_festival(festivals):
        festivals = get_festivals_data()["JP"]["data"]["festRecords"]["nodes"]
        image = get_festival(festivals)
        return image

    cnt = 0
    time_head_count = 0
    # 计算满足条件的有效数据有多少排
    for i in num_list:
        # 筛选到数据的个数
        count_match_data = 0
        if contest_match is None or contest_match == "Turf War":
            if regular[i]["regularMatchSetting"] is not None:
                if rule_match is None:
                    cnt += 1
                    count_match_data += 1
        if contest_match is None or contest_match == "Ranked Challenge":
            if ranked[i]["bankaraMatchSettings"] is not None:
                if rule_match is None or rule_match == ranked[i]["bankaraMatchSettings"][0]["vsRule"]["rule"]:
                    cnt += 1
                    count_match_data += 1
        if contest_match is None or contest_match == "Ranked Open":
            if ranked[i]["bankaraMatchSettings"] is not None:
                if rule_match is None or rule_match == ranked[i]["bankaraMatchSettings"][1]["vsRule"]["rule"]:
                    cnt += 1
                    count_match_data += 1

        if contest_match is None or contest_match == "X Schedule":
            if xschedule[i]["xMatchSetting"] is not None:
                if rule_match is None or rule_match == xschedule[i]["xMatchSetting"]["vsRule"]["rule"]:
                    cnt += 1
                    count_match_data += 1

        # 如果有筛选结果,需要加上一个时间卡片
        if count_match_data:
            time_head_count += 1

    if cnt == 0 and not have_festival(festivals):
        # 没有搜索结果情况下，用全部list再次调用自身
        num_list = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        return get_stages(schedule, num_list, contest_match, rule_match)

    time_head_bg_size = (540, 60)
    # 一张对战卡片高度为340 时间卡片高度为time_head_bg_size[1] 加上间隔为10
    background_size = (1044, 340 * cnt + (time_head_bg_size[1] + 10) * time_head_count)
    # 取背景rgb颜色
    default_bg_rgb = dict_bg_rgb["X Schedule"]
    if contest_match is not None:
        bg_rgb = dict_bg_rgb[contest_match]
    else:
        bg_rgb = default_bg_rgb
    # 创建纯色背景
    image_background = Image.new("RGBA", background_size, bg_rgb)
    bg_mask = get_file("fight_mask").resize((600, 399))
    # 填充小图蒙版
    image_background = tiled_fill(image_background, bg_mask)

    total_pos = 0
    for i in num_list:
        pos = 0
        # 创建一张纯透明图片 用来存放一个时间周期内的多张地图卡片
        background = Image.new("RGBA", background_size, (0, 0, 0, 0))
        # 筛选到数据的个数
        count_match_data = 0

        # 第一排绘制 默认为涂地模式
        if contest_match is None or contest_match == "Turf War":
            if regular[i]["regularMatchSetting"] is not None:
                if rule_match is None:
                    count_match_data += 1

                    stage = regular[i]["regularMatchSetting"]["vsStages"]
                    regular_card = get_stage_card(
                        ImageInfo(
                            stage[0]["name"],
                            stage[0]["image"]["url"],
                            get_trans_stage(stage[0]["id"]),
                            "对战地图",
                        ),
                        ImageInfo(
                            stage[1]["name"],
                            stage[1]["image"]["url"],
                            get_trans_stage(stage[1]["id"]),
                            "对战地图",
                        ),
                        "一般比赛",
                        "Regular",
                        regular[i]["regularMatchSetting"]["vsRule"]["rule"],
                        time_converter_hm(regular[i]["startTime"]),
                        time_converter_hm(regular[i]["endTime"]),
                    )
                    paste_with_a(background, regular_card, (10, pos))
                    pos += 340
                    total_pos += 340

        # 第二排绘制 默认为真格区域
        if contest_match is None or contest_match == "Ranked Challenge":
            if ranked[i]["bankaraMatchSettings"] is not None:
                if rule_match is None or rule_match == ranked[i]["bankaraMatchSettings"][0]["vsRule"]["rule"]:
                    count_match_data += 1
                    stage = ranked[i]["bankaraMatchSettings"][0]["vsStages"]
                    ranked_challenge_card = get_stage_card(
                        ImageInfo(
                            stage[0]["name"],
                            stage[0]["image"]["url"],
                            get_trans_stage(stage[0]["id"]),
                            "对战地图",
                        ),
                        ImageInfo(
                            stage[1]["name"],
                            stage[1]["image"]["url"],
                            get_trans_stage(stage[1]["id"]),
                            "对战地图",
                        ),
                        "蛮颓比赛-挑战",
                        "Ranked-Challenge",
                        ranked[i]["bankaraMatchSettings"][0]["vsRule"]["rule"],
                        time_converter_hm(ranked[i]["startTime"]),
                        time_converter_hm(ranked[i]["endTime"]),
                    )
                    paste_with_a(background, ranked_challenge_card, (10, pos))
                    pos += 340
                    total_pos += 340

        # 第三排绘制 默认为真格开放
        if contest_match is None or contest_match == "Ranked Open":
            if ranked[i]["bankaraMatchSettings"] is not None:
                if rule_match is None or rule_match == ranked[i]["bankaraMatchSettings"][1]["vsRule"]["rule"]:
                    count_match_data += 1
                    stage = ranked[i]["bankaraMatchSettings"][1]["vsStages"]
                    ranked_challenge_card = get_stage_card(
                        ImageInfo(
                            stage[0]["name"],
                            stage[0]["image"]["url"],
                            get_trans_stage(stage[0]["id"]),
                            "对战地图",
                        ),
                        ImageInfo(
                            stage[1]["name"],
                            stage[1]["image"]["url"],
                            get_trans_stage(stage[1]["id"]),
                            "对战地图",
                        ),
                        "蛮颓比赛-开放",
                        "Ranked-Open",
                        ranked[i]["bankaraMatchSettings"][1]["vsRule"]["rule"],
                        time_converter_hm(ranked[i]["startTime"]),
                        time_converter_hm(ranked[i]["endTime"]),
                    )
                    paste_with_a(background, ranked_challenge_card, (10, pos))
                    pos += 340
                    total_pos += 340

        # 第四排绘制 默认为X赛
        if contest_match is None or contest_match == "X Schedule":
            if xschedule[i]["xMatchSetting"] is not None:
                if rule_match is None or rule_match == xschedule[i]["xMatchSetting"]["vsRule"]["rule"]:
                    count_match_data += 1
                    stage = xschedule[i]["xMatchSetting"]["vsStages"]
                    ranked_challenge_card = get_stage_card(
                        ImageInfo(
                            stage[0]["name"],
                            stage[0]["image"]["url"],
                            get_trans_stage(stage[0]["id"]),
                            "对战地图",
                        ),
                        ImageInfo(
                            stage[1]["name"],
                            stage[1]["image"]["url"],
                            get_trans_stage(stage[1]["id"]),
                            "对战地图",
                        ),
                        "X比赛",
                        "X",
                        xschedule[i]["xMatchSetting"]["vsRule"]["rule"],
                        time_converter_hm(xschedule[i]["startTime"]),
                        time_converter_hm(xschedule[i]["endTime"]),
                    )
                    paste_with_a(background, ranked_challenge_card, (10, pos))
                    pos += 340
                    total_pos += 340
        # 如果有筛选结果，将时间表头贴到底图上
        if count_match_data:
            # 取涂地模式的时间，除举办祭典外，都可用
            date_time = time_converter_yd(regular[i]["startTime"])
            start_time = time_converter_hm(regular[i]["startTime"])
            end_time = time_converter_hm(regular[i]["endTime"])
            # 绘制时间表头
            time_head_bg = get_time_head_bg(time_head_bg_size, date_time, start_time, end_time)
            # 贴到大图上
            time_head_bg_pos = (
                (background_size[0] - time_head_bg_size[0]) // 2,
                total_pos - 340 * count_match_data + 10,
            )
            paste_with_a(image_background, time_head_bg, time_head_bg_pos)
            total_pos += time_head_bg_size[1] + 10

            # 将一组图片贴到底图上
            paste_with_a(
                image_background,
                background,
                (0, time_head_bg_pos[1] + time_head_bg_size[1]),
            )

    # 圆角化
    image_background = circle_corner(image_background, radii=16)
    return image_background


# 绘制 打工地图
def get_coop_stages(stage, weapon, time, boss, mode):
    # 校验是否需要绘制小鲑鱼(现在时间处于该打工时间段内)
    def check_coop_fish(_time):
        start_time = _time.split(" - ")[0]
        # 输入时间都缺少年份，需要手动补充一个年份后还原为date对象
        year = datetime.datetime.now().year
        start_time = str(year) + "-" + start_time
        now_time = datetime.datetime.now()
        st = datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M")
        if st < now_time:
            return True
        return False

    top_size_pos = (0, -2)
    bg_size = (800, len(stage) * 162 + top_size_pos[1])
    stage_bg_size = (300, 160)
    weapon_size = (90, 90)
    boss_size = (40, 40)
    mode_size = (40, 40)
    coop_fish_size = (36, 48)

    # 创建纯色背景
    image_background_rgb = dict_bg_rgb["打工"]
    image_background = Image.new("RGBA", bg_size, image_background_rgb)
    bg_mask_size = (300, 200)
    bg_mask = get_file("coop_mask").resize(bg_mask_size)
    # 填充小图蒙版
    image_background = tiled_fill(image_background, bg_mask)

    # 绘制地图信息
    coop_stage_bg = Image.new("RGBA", (bg_size[0], bg_size[1] + 2), (0, 0, 0, 0))
    dr = ImageDraw.Draw(coop_stage_bg)
    font = ImageFont.truetype(ttf_path, 30)
    for pos, val in enumerate(time):
        # 绘制时间文字
        time_text_pos = (40, 5 + pos * 160)
        time_text_size = font.getsize(val)
        dr.text(time_text_pos, val, font=font, fill="#FFFFFF")
        if check_coop_fish(val):
            # 现在时间处于打工时间段内，绘制小鲑鱼
            coop_fish_img = get_file("coop_fish").resize(coop_fish_size)
            coop_fish_img_pos = (6, 8 + pos * 160)
            paste_with_a(coop_stage_bg, coop_fish_img, coop_fish_img_pos)
    for pos, val in enumerate(stage):
        # 绘制打工地图
        stage_bg = get_save_file(val).resize(stage_bg_size, Image.ANTIALIAS)
        stage_bg_pos = (500, 2 + 162 * pos)
        coop_stage_bg.paste(stage_bg, stage_bg_pos)

        # 绘制 地图名
        stage_name_bg = get_stage_name_bg(val.zh_name, 25)
        stage_name_bg_size = stage_name_bg.size
        # X:地图x点位+一半的地图宽度-文字背景的一半宽度   Y:地图Y点位+一半地图高度-文字背景高度
        stage_name_bg_pos = (
            stage_bg_pos[0] + +stage_bg_size[0] // 2 - stage_name_bg_size[0] // 2,
            stage_bg_pos[1] + stage_bg_size[1] - stage_name_bg_size[1],
        )
        paste_with_a(coop_stage_bg, stage_name_bg, stage_name_bg_pos)

        for pos_weapon, val_weapon in enumerate(weapon[pos]):
            # 绘制武器底图
            weapon_bg_img = Image.new("RGBA", weapon_size, (30, 30, 30))
            # 绘制武器图片
            weapon_image = get_save_file(val_weapon).resize(weapon_size, Image.ANTIALIAS)
            paste_with_a(weapon_bg_img, weapon_image, (0, 0))
            coop_stage_bg.paste(weapon_bg_img, (120 * pos_weapon + 20, 60 + 160 * pos))
    for pos, val in enumerate(boss):
        if val != "":
            # 绘制boss图标
            boss_img = get_file(val).resize(boss_size)
            boss_img_pos = (500, 160 * pos + stage_bg_size[1] - 40)
            paste_with_a(coop_stage_bg, boss_img, boss_img_pos)
    for pos, val in enumerate(mode):
        # 绘制打工模式图标
        mode_img = get_file(val).resize(mode_size)
        mode_img_pos = (500 - 70, 160 * pos + 15)
        paste_with_a(coop_stage_bg, mode_img, mode_img_pos)

    paste_with_a(image_background, coop_stage_bg, top_size_pos)
    # 圆角
    image_background = circle_corner(image_background, radii=20)

    return image_background


# 绘制 随机武器
def get_random_weapon(weapon1: [WeaponData], weapon2: [WeaponData]):
    # 底图
    image_background_size = (660, 500)
    image_background = circle_corner(get_file("bg2").resize(image_background_size), radii=20)
    # 绘制上下两块武器区域
    weapon_card_bg_size = (image_background_size[0] - 10, (image_background_size[1] - 10) // 2)
    top_weapon_card = get_weapon_card(weapon1, weapon_card_bg_size, dict_bg_rgb["上-武器卡片-黄"], (34, 34, 34))
    down_weapon_card = get_weapon_card(weapon2, weapon_card_bg_size, dict_bg_rgb["下-武器卡片-蓝"], (255, 255, 255))
    # 将武器区域贴到最下层背景
    paste_with_a(image_background, top_weapon_card, (5, 5))
    paste_with_a(image_background, down_weapon_card, (5, (image_background_size[1]) // 2))
    # 绘制私房图标
    private_img_size = (35, 35)
    private_img_pos = (
        (image_background_size[0] - private_img_size[0]) // 2,
        (image_background_size[1] - private_img_size[1]) // 2,
    )
    private_img = get_file("private").resize(private_img_size)
    paste_with_a(image_background, private_img, private_img_pos)

    return image_background


# 绘制 帮助图片
def get_help():
    image_background_size = (1300, 2000)
    # 取背景rgb颜色
    bg_rgb = dict_bg_rgb["活动"]
    # 创建纯色背景
    image_background = Image.new("RGBA", image_background_size, bg_rgb)
    bg_mask = get_file("cat_paw_mask").resize((400, 250))
    # 填充小图蒙版
    image_background = tiled_fill(image_background, bg_mask)
    # 圆角
    image_background = circle_corner(image_background, radii=20)
    # 绘制标题
    font_size = 30
    text_bg = get_translucent_name_bg("帮助手册", 80, font_size)
    text_bg_size = text_bg.size
    # 贴上文字背景
    text_bg_pos = ((image_background_size[0] - text_bg_size[0]) // 2, 20)
    paste_with_a(image_background, text_bg, text_bg_pos)
    # 初始化一些参数
    drawer = ImageDraw.Draw(image_background)
    text_width = 800
    height = text_bg_pos[1] + text_bg_size[1] + 20
    title_rgb = dict_bg_rgb["祭典时间-金黄"]

    # 绘制title
    title = "对战地图 查询"
    title_pos = (20, height)
    w, h = drawer_text(drawer, title, title_pos, text_width, title_rgb)
    height += h
    # 绘制 帮助卡片 对战地图查询
    pre = "直接查询:"
    order_list = ["图", "图图", "下图", "下下图", "全部图"]
    desc_list = ["查询当前或指定时段 所有模式 的地图", "前面如果是 全部 则显示至多未来5个时段的地图"]
    text_card, card_h = drawer_help_card(pre, order_list, desc_list)
    # 贴图
    text_bg_pos = (title_pos[0] + 30, height)
    paste_with_a(image_background, text_card, text_bg_pos)
    height += card_h
    # 绘制 帮助卡片 对战地图查询
    pre = "指定时间段查询:"
    order_list = ["0图", "123图", "1图", "2468图"]
    desc_list = ["可以在前面加上多个0-9的数字，不同数字代表不同时段", "如0代表当前，1代表下时段，2代表下下时段，以此类推"]
    text_card, card_h = drawer_help_card(pre, order_list, desc_list)
    # 贴图
    text_bg_pos = (title_pos[0] + 30, height)
    paste_with_a(image_background, text_card, text_bg_pos)
    height += card_h + 10

    # 绘制title
    title = "对战地图 筛选查询"
    title_pos = (20, height)
    w, h = drawer_text(drawer, title, title_pos, text_width, title_rgb)
    height += h + 20
    # 绘制 帮助卡片 对战地图查询
    pre = "直接查询:"
    order_list = ["挑战", "涂地", "x赛", "塔楼", "开放挑战", "pp抢鱼"]
    desc_list = ["支持指定规则或比赛，或同时指定规则比赛",
                 "触发词进行了语义化处理，很多常用的称呼也能触发，如:pp和排排 都等同于 开放;抢鱼对应鱼虎;涂涂对应涂地 等"]
    text_card, card_h = drawer_help_card(pre, order_list, desc_list)
    # 贴图
    text_bg_pos = (title_pos[0] + 30, height)
    paste_with_a(image_background, text_card, text_bg_pos)
    height += card_h
    # 绘制 帮助卡片 对战地图查询
    pre = "指定时间段查询:"
    order_list = ["0挑战", "1234开放塔楼", "全部x赛区域"]
    desc_list = ["与图图的指定时间段查询方法一致，如果指定时间段没有匹配的结果，会返回全部时间段满足该筛选的结果",
                 "前面加上 全部 则显示未来24h满足条件的对战"]
    text_card, card_h = drawer_help_card(pre, order_list, desc_list)
    # 贴图
    text_bg_pos = (title_pos[0] + 30, height)
    paste_with_a(image_background, text_card, text_bg_pos)
    height += card_h

    # 绘制title
    title = "打工 查询"
    title_pos = (20, height)
    w, h = drawer_text(drawer, title, title_pos, text_width, title_rgb)
    height += h + 20
    # 绘制 帮助卡片 对战地图查询
    pre = "直接查询:"
    order_list = ["工", "打工", "bigrun", "团队打工", "全部工"]
    desc_list = ["查询当前和下一时段的打工地图，如果存在bigrun或团队打工时，也会显示在里面，并根据时间自动排序",
                 "前面加上 全部 则显示接下来的五场打工地图"]
    text_card, card_h = drawer_help_card(pre, order_list, desc_list)
    # 贴图
    text_bg_pos = (title_pos[0] + 30, height)
    paste_with_a(image_background, text_card, text_bg_pos)
    height += card_h

    # 绘制title
    title = "其他 查询"
    title_pos = (20, height)
    w, h = drawer_text(drawer, title, title_pos, text_width, title_rgb)
    height += h + 20
    # 绘制 帮助卡片 对战地图查询
    pre = "直接查询:"
    order_list = ["祭典", "活动", "衣服", "帮助", "help"]
    desc_list = ["查询 祭典  活动  nso当前售卖衣服", "帮助/help:回复本帮助图片"]
    text_card, card_h = drawer_help_card(pre, order_list, desc_list)
    # 贴图
    text_bg_pos = (title_pos[0] + 30, height)
    paste_with_a(image_background, text_card, text_bg_pos)
    height += card_h

    # 绘制title
    title = "私房用 随机武器"
    title_pos = (20, height)
    w, h = drawer_text(drawer, title, title_pos, text_width, title_rgb)
    height += h + 20
    # 绘制 帮助卡片 对战地图查询
    pre = "直接查询:"
    order_list = ["随机武器", "随机武器 nice弹", "随机武器 小枪 刷 狙 泡"]
    desc_list = [
        "可以在 随机武器 后面，接至多四个参数，每个参数间用空格分开",
        "参数包括全部的 武器类型，如 小枪 双枪 弓 狙 等;全部的 副武器名称，如 三角雷 水球 雨帘;全部的大招名称，如 nice弹 龙卷风 rpg等",
        "如果不带参数或参数小于4，剩下的会自动用 同一大类下的武器 进行筛选，如 狙 和 加特林 都属于 远程类，小枪 与 刷子，滚筒 等属于 近程类，保证尽可能公平",
        "如果不希望进行任何限制，也可以发送 随机武器完全随机，来触发不加限制的真随机武器(平衡性就没法保证了)",
    ]
    text_card, card_h = drawer_help_card(pre, order_list, desc_list)
    # 贴图
    text_bg_pos = (title_pos[0] + 30, height)
    paste_with_a(image_background, text_card, text_bg_pos)
    height += card_h

    # 绘制title
    title = "bot管理员命令"
    title_pos = (20, height)
    w, h = drawer_text(drawer, title, title_pos, text_width, (255, 167, 137))
    height += h + 20
    # 绘制 帮助卡片 对战地图查询
    pre = "直接发送:"
    order_list = ["清空图片缓存", "更新武器数据"]
    desc_list = ["清空图片缓存：会主动清空2h内的全部缓存图",
                 "更新武器数据：首次使用时，必须先运行一次这个命令，来更新武器数据库，不然随机武器功能无法使用"]
    text_card, card_h = drawer_help_card(pre, order_list, desc_list)
    # 贴图
    text_bg_pos = (title_pos[0] + 30, height)
    paste_with_a(image_background, text_card, text_bg_pos)
    height += card_h

    # # 绘制title
    # title = "关于本插件"
    # title_pos = (20, height)
    # w, h = drawer_text(drawer, title, title_pos, text_width, title_rgb)
    # height += h + 20
    # # 绘制 帮助卡片 对战地图查询
    # pre = ""
    # order_list = []
    # desc_list = [
    #     "本插件已开源，地址如下：",
    #     "https://github.com/Skyminers/Bot-Splatoon3",
    #     "有github账号的人可以去帮忙点个star，这是对我们最大的支持了",
    #     "插件作者:Cypas_Nya;Sky_miner",
    # ]
    # text_card, card_h = drawer_help_card(pre, order_list, desc_list)
    # # 贴图
    # text_bg_pos = (title_pos[0] + 30, height)
    # paste_with_a(image_background, text_card, text_bg_pos)
    # height += card_h

    return image_background


def get_gear_detail(gear):
    # 处理单件商品
    price = gear['price']
    # 售卖终止时间
    pickup_gears_sale_end_time = gear['saleEndTime']

    gear = gear['gear']
    # 处理品牌数据
    pickup_gears_brand = gear['brand']['name']
    pickup_gears_brand_key, pickup_gears_brand_cn = get_cn_name_by_en_name(BRAND_NAME_KEY, pickup_gears_brand)
    # 获取品牌容易/不容易出的技能
    usual_skill_key, unusual_skill_key = get_brand_skills(pickup_gears_brand_key, pickup_gears_brand_cn)
    diff = pickup_gears_sale_end_time - datetime.datetime.now()
    hours_remain = int(diff.total_seconds() / 3600)
    minutes_remain = int(diff.total_seconds() / 60)

    logger.debug(f'售卖终止时间: {pickup_gears_sale_end_time}, 剩余售卖小时: {hours_remain}')
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
    gear_name_key, gear_name_cn = get_cn_name_by_en_name(gear_dict[gear_type], gear['name'])
    logger.info(f'gear_name_key: {gear_name_key}, gear_name_cn: {gear_name_cn}')
    logger.debug(f'特选商品名称: {gear_name_cn}, 特选商品价格: {price}')
    # 处理商品技能
    primary_gear_power_name = gear['primaryGearPower']['name']
    primary_gear_power_name_key, primary_gear_power_name_cn = get_cn_name_by_en_name(GEAR_POWER_KEY,
                                                                                     primary_gear_power_name)
    # 仅图片为Unknown, 所以放在最后处理
    primary_gear_power_desc = CN_zh[GEAR_POWER_DESC_KEY][primary_gear_power_name_key]
    if primary_gear_power_name_key == 'None':
        primary_gear_power_name_key = 'Unknown'

    logger.debug(
        f'装备主技能: {primary_gear_power_name_cn}, 主技能效果为: {primary_gear_power_desc} ')
    skill_list = [primary_gear_power_name_key]

    # 处理商品副技能
    additional_gear_powers = gear['additionalGearPowers']
    additional_gear_power_nums = len(additional_gear_powers)
    logger.debug(f'装备副技能数量: {additional_gear_power_nums}')

    for gear_power in additional_gear_powers:
        additional_gear_power_name = gear_power['name']
        additional_gear_power_name_key, additional_gear_power_name_cn = get_cn_name_by_en_name(GEAR_POWER_KEY,
                                                                                               additional_gear_power_name)
        additional_gear_power_desc = CN_zh[GEAR_POWER_DESC_KEY][additional_gear_power_name_key]
        # 仅图片为Unknown, 所以放在最后处理
        if additional_gear_power_name_key == 'None':
            additional_gear_power_name_key = 'Unknown'
        logger.debug(
            f'装备副技能: {additional_gear_power_name_cn}, 副技能效果为: {additional_gear_power_desc}')
        skill_list.append(additional_gear_power_name_key)

    return draw_gear_pic(gear_pic_dict[gear_type] + gear_name_key, skill_list,
                         pickup_gears_brand_key, usual_skill_key, unusual_skill_key,
                         date_remain_text, str(price), gear_name_cn)


def get_cn_name_by_en_name(en_key, name):
    """
    根据英文名获取中文名
    :param en_key: 英文名字典的键
    :param name: 英文名
    :return: 中文名
    """
    # log.debug(f"英文字典为: {self.gear_trans[en_key]}")
    for k, v in EU_en[en_key].items():
        if v == name:
            return k, CN_zh[en_key][k]
    return "None", CN_zh[en_key]["None"]
