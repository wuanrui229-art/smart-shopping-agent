from __future__ import annotations


PRODUCTS = [
    {
        "id": "BP-101", "category": "backpack", "category_label": "双肩包", "brand": "TrailNest",
        "title": "TrailNest 城市通勤防水双肩包 22L", "price": 299, "rating": 4.7, "review_count": 1860,
        "features": ["防水", "轻量", "电脑隔层", "透气背板", "通勤"],
        "reviews": [
            {"rating": 5, "text": "防水面料很实用，电脑隔层有保护，通勤背一天也不累。", "verified": True, "days_ago": 4},
            {"rating": 5, "text": "拉链顺滑，分区合理，雨天没有进水。", "verified": True, "days_ago": 19},
            {"rating": 4, "text": "容量够用而且轻，侧袋如果再大一点会更好。", "verified": True, "days_ago": 37},
            {"rating": 3, "text": "肩带舒适，但浅色款比较容易脏。", "verified": False, "days_ago": 71},
            {"rating": 5, "text": "做工扎实，没有明显异味。", "verified": True, "days_ago": 103},
        ],
    },
    {
        "id": "BP-102", "category": "backpack", "category_label": "双肩包", "brand": "KiteLab",
        "title": "KiteLab 学生减负书包 18L", "price": 219, "rating": 4.6, "review_count": 2411,
        "features": ["轻量", "护脊", "反光条", "水杯袋", "学生"],
        "reviews": [
            {"rating": 5, "text": "书包很轻，护脊背板支撑不错，孩子愿意每天背。", "verified": True, "days_ago": 3},
            {"rating": 4, "text": "分层清楚，反光条晚上比较安心。", "verified": True, "days_ago": 28},
            {"rating": 4, "text": "水杯袋偏紧，大杯子不太好放。", "verified": True, "days_ago": 54},
            {"rating": 5, "text": "没有异味，肩带宽，性价比不错。", "verified": True, "days_ago": 82},
            {"rating": 3, "text": "浅色不耐脏，但整体做工可以。", "verified": False, "days_ago": 120},
        ],
    },
    {
        "id": "BP-103", "category": "backpack", "category_label": "双肩包", "brand": "UrbanArc",
        "title": "UrbanArc 商务扩容电脑背包 28L", "price": 459, "rating": 4.8, "review_count": 932,
        "features": ["防水", "扩容", "电脑隔层", "行李箱固定带", "商务"],
        "reviews": [
            {"rating": 5, "text": "扩容后短途出差够用，电脑层保护很好。", "verified": True, "days_ago": 7},
            {"rating": 5, "text": "面料防水，放在行李箱拉杆上很稳。", "verified": True, "days_ago": 33},
            {"rating": 4, "text": "收纳很多，装满后自重略明显。", "verified": True, "days_ago": 65},
            {"rating": 4, "text": "商务外观简洁，不过价格偏高。", "verified": True, "days_ago": 91},
            {"rating": 5, "text": "缝线整齐，拉链耐用。", "verified": True, "days_ago": 142},
        ],
    },
    {
        "id": "HP-201", "category": "headphones", "category_label": "蓝牙耳机", "brand": "SoundPeak",
        "title": "SoundPeak Air Pro 2 主动降噪耳机", "price": 699, "rating": 4.7, "review_count": 5204,
        "features": ["主动降噪", "通透模式", "长续航", "双设备", "通勤"],
        "reviews": [
            {"rating": 5, "text": "地铁降噪明显，人声依然自然，连接很稳定。", "verified": True, "days_ago": 2},
            {"rating": 5, "text": "续航足够一周通勤，双设备切换很方便。", "verified": True, "days_ago": 17},
            {"rating": 4, "text": "音质均衡，通话在大风环境会受一点影响。", "verified": True, "days_ago": 49},
            {"rating": 4, "text": "佩戴舒适，但充电盒容易留下划痕。", "verified": False, "days_ago": 88},
            {"rating": 5, "text": "主动降噪效果靠谱，没有明显底噪。", "verified": True, "days_ago": 134},
        ],
    },
    {
        "id": "HP-202", "category": "headphones", "category_label": "蓝牙耳机", "brand": "EchoBuds",
        "title": "EchoBuds Lite 开放式运动耳机", "price": 399, "rating": 4.5, "review_count": 3120,
        "features": ["开放式", "防汗", "轻量", "运动", "环境感知"],
        "reviews": [
            {"rating": 5, "text": "跑步很稳，能听见环境声音，安全感更好。", "verified": True, "days_ago": 5},
            {"rating": 4, "text": "很轻没有入耳胀痛，低频不如入耳式。", "verified": True, "days_ago": 31},
            {"rating": 4, "text": "防汗没问题，户外大风时声音会变薄。", "verified": True, "days_ago": 62},
            {"rating": 5, "text": "佩戴舒服，连接稳定。", "verified": True, "days_ago": 96},
            {"rating": 3, "text": "办公室漏音略明显。", "verified": False, "days_ago": 127},
        ],
    },
    {
        "id": "HP-203", "category": "headphones", "category_label": "蓝牙耳机", "brand": "NovaTune",
        "title": "NovaTune Mini 真无线耳机", "price": 229, "rating": 4.3, "review_count": 8700,
        "features": ["小巧", "低延迟", "性价比", "通话", "入耳式"],
        "reviews": [
            {"rating": 5, "text": "很好很好很好，必须买。", "verified": False, "days_ago": 1},
            {"rating": 5, "text": "很好很好很好，必须买。", "verified": False, "days_ago": 1},
            {"rating": 5, "text": "很好很好很好，必须买。", "verified": False, "days_ago": 1},
            {"rating": 2, "text": "右耳偶尔断连，售后换货后才恢复。", "verified": True, "days_ago": 84},
            {"rating": 3, "text": "便宜但降噪一般，通话够用。", "verified": True, "days_ago": 126},
        ],
    },
    {
        "id": "SH-301", "category": "running_shoes", "category_label": "跑鞋", "brand": "PaceFlow",
        "title": "PaceFlow Daily 5 缓震跑鞋", "price": 529, "rating": 4.8, "review_count": 2208,
        "features": ["缓震", "透气", "日常训练", "轻量", "耐磨"],
        "reviews": [
            {"rating": 5, "text": "缓震柔和但不泄力，适合日常五到十公里。", "verified": True, "days_ago": 6},
            {"rating": 5, "text": "鞋面透气，尺码正常，后跟锁定稳定。", "verified": True, "days_ago": 26},
            {"rating": 4, "text": "湿地抓地一般，其他方面都很均衡。", "verified": True, "days_ago": 57},
            {"rating": 5, "text": "跑了两百公里鞋底磨损不明显。", "verified": True, "days_ago": 97},
            {"rating": 4, "text": "宽脚建议大半码。", "verified": False, "days_ago": 151},
        ],
    },
    {
        "id": "SH-302", "category": "running_shoes", "category_label": "跑鞋", "brand": "StrideLab",
        "title": "StrideLab Tempo 竞速训练鞋", "price": 799, "rating": 4.7, "review_count": 1184,
        "features": ["回弹", "竞速", "轻量", "推进感", "训练"],
        "reviews": [
            {"rating": 5, "text": "回弹明显，节奏跑推进感好。", "verified": True, "days_ago": 9},
            {"rating": 5, "text": "重量轻，鞋面包裹紧致。", "verified": True, "days_ago": 39},
            {"rating": 4, "text": "适合有经验的跑者，慢跑时不算柔软。", "verified": True, "days_ago": 73},
            {"rating": 4, "text": "耐磨中等，价格略高。", "verified": True, "days_ago": 111},
            {"rating": 5, "text": "十公里比赛发挥稳定。", "verified": False, "days_ago": 166},
        ],
    },
    {
        "id": "SH-303", "category": "running_shoes", "category_label": "跑鞋", "brand": "EasyRun",
        "title": "EasyRun Comfort 入门慢跑鞋", "price": 329, "rating": 4.5, "review_count": 4096,
        "features": ["缓震", "宽楦", "入门", "慢跑", "性价比"],
        "reviews": [
            {"rating": 5, "text": "宽脚穿着舒服，入门慢跑足够。", "verified": True, "days_ago": 11},
            {"rating": 4, "text": "缓震舒适，鞋子稍微偏重。", "verified": True, "days_ago": 44},
            {"rating": 4, "text": "价格合适，鞋面夏天略闷。", "verified": True, "days_ago": 79},
            {"rating": 5, "text": "尺码准确，走路跑步都可以。", "verified": True, "days_ago": 123},
            {"rating": 4, "text": "后跟支撑不错。", "verified": False, "days_ago": 180},
        ],
    },
]


CATEGORY_ALIASES = {
    "backpack": ["书包", "背包", "双肩包", "backpack", "school bag"],
    "headphones": ["耳机", "蓝牙耳机", "降噪耳机", "headphone", "earbud"],
    "running_shoes": ["跑鞋", "运动鞋", "慢跑鞋", "running shoes", "sneaker"],
}

CATEGORY_LABELS = {"backpack": "双肩包", "headphones": "蓝牙耳机", "running_shoes": "跑鞋"}
