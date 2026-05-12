#!/usr/bin/env python3
"""Generate static recommendation tags for all public restaurant records.

The output intentionally separates factual tags from inferred tags.  Factual
tags are derived directly from the source JSON; inferred tags are conservative
rule-based priors from category, area, selection history, and shop-name cues.
No network calls are made.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import unicodedata
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATASETS = (
    ROOT / "data" / "udon.json",
    ROOT / "data" / "soba.json",
)
DATA_VERSION = ROOT / "data" / "data-version.json"
EXTERNAL_SIGNALS = ROOT / "data" / "external_signals.json"
OUTPUT = ROOT / "data" / "recommendation_tags.json"

MIN_CONFIDENCE_TO_OUTPUT = 0.45

SOURCE_RANK = {
    "data": 5,
    "external_signal": 4,
    "name_keyword": 4,
    "selection_prior": 3,
    "regional_prior": 2,
    "model_prior": 1,
}

PREFECTURE_SLUGS = {
    "北海道": "hokkaido",
    "青森県": "aomori",
    "岩手県": "iwate",
    "宮城県": "miyagi",
    "秋田県": "akita",
    "山形県": "yamagata",
    "福島県": "fukushima",
    "茨城県": "ibaraki",
    "栃木県": "tochigi",
    "群馬県": "gunma",
    "埼玉県": "saitama",
    "千葉県": "chiba",
    "東京都": "tokyo",
    "神奈川県": "kanagawa",
    "新潟県": "niigata",
    "富山県": "toyama",
    "石川県": "ishikawa",
    "福井県": "fukui",
    "山梨県": "yamanashi",
    "長野県": "nagano",
    "岐阜県": "gifu",
    "静岡県": "shizuoka",
    "愛知県": "aichi",
    "三重県": "mie",
    "滋賀県": "shiga",
    "京都府": "kyoto",
    "大阪府": "osaka",
    "兵庫県": "hyogo",
    "奈良県": "nara",
    "和歌山県": "wakayama",
    "鳥取県": "tottori",
    "島根県": "shimane",
    "岡山県": "okayama",
    "広島県": "hiroshima",
    "山口県": "yamaguchi",
    "徳島県": "tokushima",
    "香川県": "kagawa",
    "愛媛県": "ehime",
    "高知県": "kochi",
    "福岡県": "fukuoka",
    "佐賀県": "saga",
    "長崎県": "nagasaki",
    "熊本県": "kumamoto",
    "大分県": "oita",
    "宮崎県": "miyazaki",
    "鹿児島県": "kagoshima",
    "沖縄県": "okinawa",
}

MACRO_AREAS = {
    "hokkaido_tohoku": {"北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県"},
    "kanto": {"茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県", "山梨県"},
    "chubu": {"新潟県", "富山県", "石川県", "福井県", "長野県", "岐阜県", "静岡県", "愛知県"},
    "kansai": {"三重県", "滋賀県", "京都府", "大阪府", "兵庫県", "奈良県", "和歌山県"},
    "chugoku_shikoku": {"鳥取県", "島根県", "岡山県", "広島県", "山口県", "徳島県", "香川県", "愛媛県", "高知県"},
    "kyushu_okinawa": {"福岡県", "佐賀県", "長崎県", "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県"},
}

TAG_DEFINITIONS: dict[str, dict[str, str]] = {
    "genre.udon": {"label": "うどん", "kind": "fact"},
    "genre.soba": {"label": "そば", "kind": "fact"},
    "region.east": {"label": "EAST", "kind": "fact"},
    "region.west": {"label": "WEST", "kind": "fact"},
    "region.kagawa": {"label": "KAGAWA", "kind": "fact"},
    "macro_area.hokkaido_tohoku": {"label": "北海道・東北", "kind": "fact"},
    "macro_area.kanto": {"label": "関東・山梨", "kind": "fact"},
    "macro_area.chubu": {"label": "中部・北陸", "kind": "fact"},
    "macro_area.kansai": {"label": "関西・三重", "kind": "fact"},
    "macro_area.chugoku_shikoku": {"label": "中国・四国", "kind": "fact"},
    "macro_area.kyushu_okinawa": {"label": "九州・沖縄", "kind": "fact"},
    "status.open": {"label": "営業中", "kind": "fact"},
    "status.closed_or_moved": {"label": "閉店・移転", "kind": "fact"},
    "selection.once": {"label": "1回選出", "kind": "fact"},
    "selection.repeat": {"label": "複数回選出", "kind": "fact"},
    "selection.strong_repeat": {"label": "3回以上選出", "kind": "fact"},
    "selection.hall_of_fame_relative": {"label": "殿堂入り相当（カテゴリ上位10%）", "kind": "fact"},
    "selection.latest_new": {"label": "最新年度で初登場", "kind": "fact"},
    "style.handmade": {"label": "手打ち・自家製寄り", "kind": "inferred"},
    "style.regional_specialty": {"label": "地域色が強い", "kind": "inferred"},
    "style.sanuki_influenced": {"label": "讃岐系の傾向", "kind": "inferred"},
    "style.musashino_udon": {"label": "武蔵野うどん系", "kind": "inferred"},
    "style.yoshida_udon": {"label": "吉田うどん系", "kind": "inferred"},
    "style.kansai_dashi": {"label": "関西だし寄り", "kind": "inferred"},
    "style.hakata_udon": {"label": "博多・福岡うどん系", "kind": "inferred"},
    "style.edomae_soba": {"label": "江戸前そば系", "kind": "inferred"},
    "style.shinshu_soba": {"label": "信州そば系", "kind": "inferred"},
    "style.echizen_soba": {"label": "越前そば系", "kind": "inferred"},
    "style.izumo_soba": {"label": "出雲そば系", "kind": "inferred"},
    "style.country_soba": {"label": "田舎そば寄り", "kind": "inferred"},
    "style.stone_milled": {"label": "石臼・玄蕎麦寄り", "kind": "inferred"},
    "style.self_service": {"label": "セルフ・短時間寄り", "kind": "inferred"},
    "texture.koshi_strong": {"label": "コシ重視寄り", "kind": "inferred"},
    "texture.aroma_focused": {"label": "香り重視寄り", "kind": "inferred"},
    "texture.throat_smooth": {"label": "喉越し重視寄り", "kind": "inferred"},
    "dish.curry": {"label": "カレー系", "kind": "inferred"},
    "dish.kamaage": {"label": "釜揚げ系", "kind": "inferred"},
    "dish.kamatama": {"label": "釜玉系", "kind": "inferred"},
    "dish.bukkake": {"label": "ぶっかけ系", "kind": "inferred"},
    "dish.meat_soup": {"label": "肉汁・肉うどん系", "kind": "inferred"},
    "dish.miso_nikomi": {"label": "味噌煮込み系", "kind": "inferred"},
    "dish.kishimen": {"label": "きしめん系", "kind": "inferred"},
    "dish.inaniwa": {"label": "稲庭うどん系", "kind": "inferred"},
    "dish.duck": {"label": "鴨系", "kind": "inferred"},
    "dish.tempura": {"label": "天ぷら系", "kind": "inferred"},
    "dish.juwari": {"label": "十割そば系", "kind": "inferred"},
    "scene.solo_lunch": {"label": "一人昼食向き", "kind": "inferred"},
    "scene.quick_lunch": {"label": "短時間利用向き", "kind": "inferred"},
    "scene.destination": {"label": "目的地として訪ねる店", "kind": "inferred"},
    "scene.drink_pairing": {"label": "酒・蕎麦前寄り", "kind": "inferred"},
    "scene.calm_meal": {"label": "落ち着いた食事向き", "kind": "inferred"},
    "mood.traditional": {"label": "伝統・老舗感", "kind": "inferred"},
    "mood.modern": {"label": "現代的・個性派", "kind": "inferred"},
    "lineage.okina": {"label": "翁・達磨系の連想", "kind": "inferred"},
    "lineage.yabu": {"label": "藪・竹やぶ系の連想", "kind": "inferred"},
    "lineage.sarashina": {"label": "更科系の連想", "kind": "inferred"},
    "lineage.sunaba": {"label": "砂場系の連想", "kind": "inferred"},
}

COMMON_KEYWORD_RULES = (
    ("style.handmade", ("手打", "手打ち", "本手打", "純手打", "手造り", "自家製", "石臼挽", "製麺所"), 0.82, 0.86),
    ("style.self_service", ("セルフ",), 0.75, 0.86),
    ("scene.drink_pairing", ("酒", "居酒屋", "蕎麦前", "醸し", "バル"), 0.68, 0.76),
    ("mood.modern", ("JAZZ", "ジャズ", "スタンド", "バル", "cafe", "CAFE", "カフェ"), 0.55, 0.62),
    ("mood.traditional", ("総本家", "元祖", "本店", "本陣", "傳", "伝統", "老舗"), 0.56, 0.62),
)

UDON_KEYWORD_RULES = (
    ("style.sanuki_influenced", ("讃岐", "さぬき", "饂飩", "うどん職人さぬき"), 0.90, 0.84),
    ("style.musashino_udon", ("武蔵野",), 0.90, 0.88),
    ("style.yoshida_udon", ("吉田",), 0.86, 0.78),
    ("dish.curry", ("カレー", "かれー", "こんぴら茶屋", "糸庄"), 0.86, 0.88),
    ("dish.kamaage", ("釜あげ", "釜揚", "釜たけ", "釜竹", "釜ひろ", "釜喜利", "釜善"), 0.82, 0.84),
    ("dish.kamatama", ("釜玉",), 0.86, 0.9),
    ("dish.bukkake", ("ぶっかけ",), 0.82, 0.88),
    ("dish.meat_soup", ("肉汁", "肉うどん", "肉 甚三", "肉汁うどん"), 0.76, 0.8),
    ("dish.miso_nikomi", ("味噌煮込", "味噌煮込み", "味噌"), 0.86, 0.86),
    ("dish.kishimen", ("きしめん",), 0.88, 0.92),
    ("dish.inaniwa", ("稲庭",), 0.88, 0.9),
    ("dish.tempura", ("天ぷら", "天ざる", "天釜", "天丼"), 0.66, 0.72),
    ("style.kansai_dashi", ("京うどん",), 0.68, 0.72),
)

SOBA_KEYWORD_RULES = (
    ("dish.juwari", ("十割", "生粉打"), 0.88, 0.9),
    ("dish.duck", ("鴨",), 0.78, 0.82),
    ("dish.tempura", ("天ぷら", "天せいろ", "天ざる"), 0.68, 0.76),
    ("style.stone_milled", ("石臼", "手挽き", "玄蕎麦", "玄そば", "玄水"), 0.78, 0.78),
    ("style.edomae_soba", ("藪", "やぶ", "砂場", "更科", "室町", "並木", "蕎麦切り", "そば切り"), 0.85, 0.82),
    ("lineage.okina", ("翁", "達磨"), 0.72, 0.74),
    ("lineage.yabu", ("藪", "やぶ", "竹やぶ"), 0.74, 0.78),
    ("lineage.sarashina", ("更科",), 0.74, 0.8),
    ("lineage.sunaba", ("砂場",), 0.74, 0.8),
)


# Editorial model priors used as a light pairwise signal on top of tag similarity.
# These are not facts about the shops. They encode broad exploration contexts such
# as "Tokyo Sanuki-style udon" or "Yabu/Edomae soba lineage" so the runtime can
# nudge plausible candidates without hard-coding deterministic recommendations.
AFFINITY_GROUPS = (
    {
        "id": "tokyo_sanuki_udon",
        "label": "東京の讃岐・手打ちうどん文脈",
        "category": "udon",
        "modes": ("similar", "nearby"),
        "boost": 0.08,
        "names": (
            "うどん 丸香",
            "うどん 慎",
            "讃岐うどん いわい",
            "讃岐うどん 蔵之介",
            "香川 一福 神田店",
            "手打うどん すみた",
            "純手打ち讃岐うどん五郎",
            "切麦や 甚六",
        ),
    },
    {
        "id": "tokyo_quick_udon",
        "label": "都内で短時間利用しやすいうどん文脈",
        "category": "udon",
        "modes": ("similar", "nearby"),
        "boost": 0.07,
        "names": (
            "おにやんま 五反田本店",
            "おにやんま 新橋店",
            "おにやんま 人形町店",
            "おにやんま 中目黒店",
            "おにやんま 東品川店",
            "自家製さぬきうどんと肉 甚三 大門店",
            "こくわがた",
            "トウキョウライトブルー ホンゴウスリー",
        ),
    },
    {
        "id": "kamaage_udon",
        "label": "釜揚げ・釜系うどん文脈",
        "category": "udon",
        "modes": ("similar", "expand"),
        "boost": 0.1,
        "names": (
            "根津 釜竹",
            "釜あげうどん はつとみ",
            "難波千日前 釜たけうどん 八重洲北口店",
            "釜揚うどん一紀",
            "釜ひろ",
            "釜あげうどん 長田 in 香の香",
            "長田うどん",
            "釜揚げうどん専門店もと",
        ),
    },
    {
        "id": "nagoya_udon",
        "label": "名古屋・愛知のうどん文脈",
        "category": "udon",
        "modes": ("similar", "nearby"),
        "boost": 0.09,
        "names": (
            "うどん 錦",
            "めん専門店 味良",
            "手打うどん かとう",
            "うどん料理 千",
            "きしや",
            "玉川 豊橋広小路本店",
            "讃州手打ちうどん 我龍",
            "酒と味噌煮込み 味噌煮込罠",
        ),
    },
    {
        "id": "osaka_sanuki_udon",
        "label": "大阪の讃岐・剛麺系うどん文脈",
        "category": "udon",
        "modes": ("similar", "nearby"),
        "boost": 0.08,
        "names": (
            "讃岐うどん 白庵",
            "手造りうどん 楽々",
            "極楽うどん TKU",
            "極楽うどん Ah-麺",
            "たけうちうどん店",
            "踊るうどん 滝井本店",
            "讃岐うどん 今雪",
            "空飛ぶうどん やまぶき家",
        ),
    },
    {
        "id": "kyoto_kansai_udon",
        "label": "京都・関西だしうどん文脈",
        "category": "udon",
        "modes": ("similar", "expand"),
        "boost": 0.08,
        "names": (
            "山元麺蔵",
            "本格手打うどん 大河",
            "京うどん 生蕎麦 岡北",
            "日の出うどん",
            "仁王門 うね乃",
            "道頓堀 今井 本店",
            "うどん棒 大阪本店",
        ),
    },
    {
        "id": "kagawa_udon_pilgrimage",
        "label": "香川の讃岐うどん巡り文脈",
        "category": "udon",
        "modes": ("similar", "nearby", "expand"),
        "boost": 0.09,
        "names": (
            "山越うどん",
            "手打うどん たむら",
            "中村うどん",
            "日の出製麺所",
            "讃岐うどん がもう",
            "須崎食料品店",
            "谷川米穀店",
            "山内うどん店",
            "純手打うどん よしや",
            "本格手打うどん おか泉",
            "竹清 本店",
            "うどん本陣 山田家 讃岐本店",
        ),
    },
    {
        "id": "musashino_udon",
        "label": "武蔵野うどん・肉汁うどん文脈",
        "category": "udon",
        "modes": ("similar", "nearby"),
        "boost": 0.1,
        "names": (
            "うちたて家",
            "むさしの エン座",
            "小平うどん 小平本店",
            "村山 満月うどん",
            "豚や",
            "武蔵野うどん 藤原 北与野本店",
            "田舎うどん てつ",
        ),
    },
    {
        "id": "yoshida_udon",
        "label": "吉田うどん文脈",
        "category": "udon",
        "modes": ("similar", "nearby"),
        "boost": 0.11,
        "names": (
            "麺許皆伝",
            "みうらうどん",
            "桜井うどん",
            "手打ちうどん ムサシ",
        ),
    },
    {
        "id": "inaniwa_udon",
        "label": "稲庭うどん・喉越しうどん文脈",
        "category": "udon",
        "modes": ("similar", "expand"),
        "boost": 0.1,
        "names": (
            "銀座 佐藤養助",
            "佐藤養助 秋田店",
            "稲庭うどんとめし 金子半之助 コレド室町店",
        ),
    },
    {
        "id": "hakata_kyushu_udon",
        "label": "博多・九州うどん文脈",
        "category": "udon",
        "modes": ("similar", "nearby", "expand"),
        "boost": 0.09,
        "names": (
            "葉隠うどん",
            "うどん平",
            "釜喜利うどん",
            "博多うどん酒場イチカバチカ 恵比寿店",
            "ふたみうどん研究所",
            "釜揚げうどん 織田薪 本店",
        ),
    },
    {
        "id": "curry_regional_udon",
        "label": "カレー・変化球うどん文脈",
        "category": "udon",
        "modes": ("similar", "expand"),
        "boost": 0.09,
        "names": (
            "こんぴら茶屋",
            "カレーうどん 鯱乃家",
            "糸庄 本店",
            "酒と味噌煮込み 味噌煮込罠",
        ),
    },
    {
        "id": "tokyo_handmade_soba",
        "label": "東京の手打ち・石臼そば文脈",
        "category": "soba",
        "modes": ("similar", "nearby"),
        "boost": 0.08,
        "names": (
            "石臼挽き手打 蕎楽亭",
            "玉笑",
            "手打蕎麦 松永",
            "蕎麦 たじま",
            "手打ち蕎麦 成冨",
            "一東菴",
            "手打蕎麦 じゆうさん",
            "蕎麦 流石",
            "木挽町 湯津上屋",
        ),
    },
    {
        "id": "tokyo_soba_drink_pairing",
        "label": "東京の蕎麦前・酒とそば文脈",
        "category": "soba",
        "modes": ("similar", "expand"),
        "boost": 0.08,
        "names": (
            "蕎麦切り 酒 大愚",
            "眠庵",
            "浅草じゅうろく",
            "ら すとらあだ",
            "神楽坂 大川や",
            "巽蕎麦 志ま平",
        ),
    },
    {
        "id": "yabu_edomae_soba",
        "label": "藪・江戸前そば系譜文脈",
        "category": "soba",
        "modes": ("similar", "expand"),
        "boost": 0.1,
        "names": (
            "竹やぶ 柏本店",
            "千寿 竹やぶ",
            "竹やぶ 箱根店",
            "吾妻橋 やぶそば",
            "並木藪蕎麦",
            "薮蕎麦 宮本",
            "江戸蕎麦ほそ川",
        ),
    },
    {
        "id": "okina_soba",
        "label": "翁・達磨系のそば文脈",
        "category": "soba",
        "modes": ("similar", "expand"),
        "boost": 0.1,
        "names": (
            "狭山 翁",
            "伊達 翁",
            "蕎麦 ふじおか",
            "手打蕎麦 わくり",
            "玄",
            "蕎麦 たかま",
        ),
    },
    {
        "id": "shinshu_soba",
        "label": "信州そば・目的地型そば文脈",
        "category": "soba",
        "modes": ("similar", "expand"),
        "boost": 0.09,
        "names": (
            "うずら家",
            "せきざわ",
            "そばの実",
            "三城",
            "丸富",
            "石臼挽き蕎麦香房 山の実",
            "職人館",
            "蕎麦 ふじおか",
        ),
    },
    {
        "id": "kansai_soba",
        "label": "関西の落ち着いた手打ちそば文脈",
        "category": "soba",
        "modes": ("similar", "nearby"),
        "boost": 0.08,
        "names": (
            "手打ち蕎麦 かね井",
            "おがわ",
            "まつもと",
            "蕎麦 たかま",
            "手打そば 乃田",
            "そば切り 岳空",
            "玄",
            "ろあん松田 篠山店",
        ),
    },
    {
        "id": "kanagawa_destination_soba",
        "label": "神奈川の目的地型そば文脈",
        "category": "soba",
        "modes": ("similar", "nearby"),
        "boost": 0.08,
        "names": (
            "蕎麦 惠土",
            "オリベ",
            "蕎房 猪口屋",
            "竹やぶ 箱根店",
        ),
    },
    {
        "id": "chiba_boso_destination_soba",
        "label": "千葉・房総の目的地型そば文脈",
        "category": "soba",
        "modes": ("similar", "nearby"),
        "boost": 0.08,
        "names": (
            "手造りそば 打墨庵 加瀬",
            "流山 すず季",
            "竹やぶ 柏本店",
            "慈久庵",
        ),
    },
    {
        "id": "north_kanto_country_soba",
        "label": "北関東の田舎そば・目的地そば文脈",
        "category": "soba",
        "modes": ("similar", "expand"),
        "boost": 0.09,
        "names": (
            "凡味 そばきり",
            "手打ちそば 舞鶴",
            "慈久庵",
            "鯨荘 塩町館",
            "木挽庵",
            "手打ちそば 梅蕎麦",
            "蕎麦切り あなざわ",
        ),
    },
    {
        "id": "chubu_hokuriku_soba",
        "label": "中部・北陸の石臼手打ちそば文脈",
        "category": "soba",
        "modes": ("similar", "expand"),
        "boost": 0.08,
        "names": (
            "草庵",
            "蕎麦正まつい",
            "仲佐",
            "手打蕎麦 わくり",
            "胡蝶庵 仙波",
            "手挽きそば 一心",
            "玄水",
        ),
    },
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_text(value: object) -> str:
    return unicodedata.normalize("NFKC", str(value or "")).strip()


def tag_key_pref(prefecture: str) -> str:
    slug = PREFECTURE_SLUGS.get(prefecture, re.sub(r"\W+", "_", prefecture).strip("_").lower())
    return f"pref.{slug}"


def macro_area_for(prefecture: str) -> str | None:
    for key, prefs in MACRO_AREAS.items():
        if prefecture in prefs:
            return key
    return None


def add_definition(key: str, label: str, kind: str) -> None:
    TAG_DEFINITIONS.setdefault(key, {"label": label, "kind": kind})


def add_tag(
    tags: dict[str, dict[str, Any]],
    key: str,
    weight: float,
    confidence: float,
    source: str,
    evidence: str,
) -> None:
    if confidence < MIN_CONFIDENCE_TO_OUTPUT:
        return
    current = tags.get(key)
    payload = {
        "key": key,
        "weight": round(min(max(weight, 0.0), 1.0), 2),
        "confidence": round(min(max(confidence, 0.0), 1.0), 2),
        "source": source,
        "evidence": [evidence],
    }
    if current is None:
        tags[key] = payload
        return

    current_strength = current["weight"] * current["confidence"]
    new_strength = payload["weight"] * payload["confidence"]
    if new_strength > current_strength or (
        math.isclose(new_strength, current_strength) and SOURCE_RANK[source] > SOURCE_RANK[current["source"]]
    ):
        payload["evidence"] = sorted(set(current["evidence"] + payload["evidence"]))
        tags[key] = payload
    elif evidence not in current["evidence"]:
        current["evidence"].append(evidence)
        current["evidence"].sort()


def apply_keyword_rules(tags: dict[str, dict[str, Any]], text: str, rules: tuple[tuple[str, tuple[str, ...], float, float], ...]) -> None:
    for key, keywords, weight, confidence in rules:
        for keyword in keywords:
            if key == "dish.duck" and keyword == "鴨" and "鴨" not in text.replace("巣鴨", ""):
                continue
            if keyword in text:
                add_tag(tags, key, weight, confidence, "name_keyword", f"name_keyword:{keyword}")
                break


def hall_of_fame_threshold(restaurants: list[dict[str, Any]], category: str) -> int:
    counts = sorted((len(r.get("years") or []) for r in restaurants if r.get("category") == category), reverse=True)
    if not counts:
        return 99
    index = max(0, math.ceil(len(counts) * 0.10) - 1)
    return max(1, counts[index])


def build_affinity_groups(restaurants: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_name = {normalize_text(restaurant.get("name")): restaurant for restaurant in restaurants}
    groups: list[dict[str, Any]] = []
    for group in AFFINITY_GROUPS:
        urls: list[str] = []
        missing: list[str] = []
        for name in group["names"]:
            restaurant = by_name.get(normalize_text(name))
            if restaurant:
                urls.append(restaurant["url"])
            else:
                missing.append(name)
        if len(urls) < 2:
            continue
        groups.append(
            {
                "id": group["id"],
                "label": group["label"],
                "category": group["category"],
                "modes": list(group["modes"]),
                "boost": group["boost"],
                "urls": urls,
                "missingNames": missing,
            }
        )
    return groups


def build_tags_for_restaurant(
    restaurant: dict[str, Any],
    thresholds: dict[str, int],
    external_signal_index: dict[str, list[dict[str, Any]]] | None = None,
) -> list[dict[str, Any]]:
    tags: dict[str, dict[str, Any]] = {}
    category = restaurant["category"]
    region = str(restaurant["region"]).lower()
    prefecture = restaurant["prefecture"]
    name = normalize_text(restaurant.get("name"))
    area = normalize_text(restaurant.get("area"))
    address = normalize_text(restaurant.get("address"))
    select_count = len(restaurant.get("years") or [])

    add_tag(tags, f"genre.{category}", 1.0, 1.0, "data", "category")
    add_tag(tags, f"region.{region}", 1.0, 1.0, "data", "region")
    pref_key = tag_key_pref(prefecture)
    add_definition(pref_key, prefecture, "fact")
    add_tag(tags, pref_key, 0.8, 1.0, "data", "prefecture")
    macro_area = macro_area_for(prefecture)
    if macro_area:
        add_tag(tags, f"macro_area.{macro_area}", 0.72, 1.0, "data", "prefecture")
    add_tag(tags, "status.closed_or_moved" if restaurant.get("closed") else "status.open", 1.0, 1.0, "data", "closed")

    if select_count <= 1:
        add_tag(tags, "selection.once", 0.42, 1.0, "data", "years")
    else:
        add_tag(tags, "selection.repeat", 0.6, 1.0, "data", "years")
    if select_count >= 3:
        add_tag(tags, "selection.strong_repeat", 0.72, 1.0, "data", "years")
    if select_count >= thresholds[category]:
        add_tag(tags, "selection.hall_of_fame_relative", 0.86, 1.0, "data", "category_top10_threshold")
        add_tag(tags, "scene.destination", 0.78, 0.72, "selection_prior", "selection:category_top10")
    elif select_count >= 3:
        add_tag(tags, "scene.destination", 0.66, 0.62, "selection_prior", "selection:3plus")
    if restaurant.get("firstSelected"):
        add_tag(tags, "selection.latest_new", 0.55, 1.0, "data", "firstSelected")

    if area.endswith("駅") or "駅" in area:
        add_tag(tags, "scene.solo_lunch", 0.52, 0.56, "regional_prior", "area:station")
        add_tag(tags, "scene.quick_lunch", 0.48, 0.5, "regional_prior", "area:station")

    apply_keyword_rules(tags, name, COMMON_KEYWORD_RULES)

    if category == "udon":
        add_tag(tags, "scene.solo_lunch", 0.48, 0.5, "model_prior", "category:udon")
        add_tag(tags, "texture.koshi_strong", 0.58, 0.5, "model_prior", "category:udon")
        apply_keyword_rules(tags, name, UDON_KEYWORD_RULES)
        if restaurant["region"] == "KAGAWA" or prefecture == "香川県":
            add_tag(tags, "style.sanuki_influenced", 0.9, 0.86, "regional_prior", "region:kagawa")
            add_tag(tags, "texture.koshi_strong", 0.78, 0.72, "regional_prior", "region:kagawa")
            add_tag(tags, "style.regional_specialty", 0.78, 0.76, "regional_prior", "region:kagawa")
            add_tag(tags, "scene.destination", 0.7, 0.62, "regional_prior", "region:kagawa")
        if prefecture in {"大阪府", "京都府", "兵庫県", "奈良県", "滋賀県", "和歌山県"}:
            add_tag(tags, "style.kansai_dashi", 0.55, 0.52, "regional_prior", "macro_area:kansai")
        if prefecture == "福岡県" or any(keyword in name for keyword in ("博多", "葉隠うどん", "うどん平")):
            add_tag(tags, "style.hakata_udon", 0.78, 0.72, "regional_prior", "prefecture_or_name:hakata_udon")
            add_tag(tags, "texture.throat_smooth", 0.62, 0.62, "regional_prior", "prefecture_or_name:hakata_udon")
            add_tag(tags, "style.regional_specialty", 0.7, 0.68, "regional_prior", "prefecture_or_name:hakata_udon")
        if "佐藤養助" in name:
            add_tag(tags, "dish.inaniwa", 0.9, 0.88, "name_keyword", "name_keyword:佐藤養助")
            add_tag(tags, "texture.throat_smooth", 0.72, 0.7, "name_keyword", "name_keyword:佐藤養助")
            add_tag(tags, "scene.calm_meal", 0.62, 0.62, "name_keyword", "name_keyword:佐藤養助")
        if prefecture == "京都府":
            add_tag(tags, "style.kansai_dashi", 0.62, 0.62, "regional_prior", "prefecture:kyoto_udon")
            add_tag(tags, "scene.destination", 0.64, 0.6, "regional_prior", "prefecture:kyoto_udon")
        if any(keyword in name for keyword in ("製麺所", "食料品店", "セルフ")):
            add_tag(tags, "style.self_service", 0.74, 0.78, "name_keyword", "name_keyword:production_or_self_service")
            add_tag(tags, "scene.quick_lunch", 0.62, 0.68, "name_keyword", "name_keyword:production_or_self_service")
            add_tag(tags, "style.regional_specialty", 0.68, 0.68, "name_keyword", "name_keyword:production_or_self_service")
        if prefecture == "山梨県" or "吉田" in name:
            add_tag(tags, "style.yoshida_udon", 0.82, 0.76, "regional_prior", "prefecture:yamanashi")
            add_tag(tags, "style.regional_specialty", 0.74, 0.72, "regional_prior", "prefecture:yamanashi")
        if "武蔵野" in name:
            add_tag(tags, "texture.koshi_strong", 0.8, 0.76, "name_keyword", "name_keyword:武蔵野")
            add_tag(tags, "style.regional_specialty", 0.7, 0.76, "name_keyword", "name_keyword:武蔵野")
        if "讃岐" in name or "さぬき" in name:
            add_tag(tags, "texture.koshi_strong", 0.84, 0.78, "name_keyword", "name_keyword:讃岐/さぬき")
            add_tag(tags, "style.regional_specialty", 0.7, 0.7, "name_keyword", "name_keyword:讃岐/さぬき")

    if category == "soba":
        add_tag(tags, "scene.calm_meal", 0.56, 0.56, "model_prior", "category:soba")
        add_tag(tags, "texture.aroma_focused", 0.68, 0.58, "model_prior", "category:soba")
        add_tag(tags, "texture.throat_smooth", 0.5, 0.5, "model_prior", "category:soba")
        apply_keyword_rules(tags, name, SOBA_KEYWORD_RULES)
        if prefecture == "東京都":
            add_tag(tags, "style.edomae_soba", 0.58, 0.56, "regional_prior", "prefecture:tokyo")
        if prefecture in {"京都府", "大阪府", "奈良県", "兵庫県"}:
            add_tag(tags, "scene.calm_meal", 0.6, 0.6, "regional_prior", "macro_area:kansai_soba")
            add_tag(tags, "texture.aroma_focused", 0.62, 0.6, "regional_prior", "macro_area:kansai_soba")
        if prefecture == "長野県":
            add_tag(tags, "style.shinshu_soba", 0.86, 0.78, "regional_prior", "prefecture:nagano")
            add_tag(tags, "style.regional_specialty", 0.78, 0.76, "regional_prior", "prefecture:nagano")
            add_tag(tags, "texture.aroma_focused", 0.76, 0.72, "regional_prior", "prefecture:nagano")
        if prefecture == "福井県":
            add_tag(tags, "style.echizen_soba", 0.84, 0.74, "regional_prior", "prefecture:fukui")
            add_tag(tags, "style.regional_specialty", 0.76, 0.74, "regional_prior", "prefecture:fukui")
        if prefecture == "島根県" or "出雲" in name:
            add_tag(tags, "style.izumo_soba", 0.84, 0.74, "regional_prior", "prefecture:shimane_or_name")
            add_tag(tags, "style.regional_specialty", 0.76, 0.74, "regional_prior", "prefecture:shimane_or_name")
        if prefecture in {"山形県", "茨城県", "栃木県", "群馬県"} or "田舎" in name:
            add_tag(tags, "style.country_soba", 0.62, 0.62, "regional_prior", "country_soba_prior")
        if any(keyword in name for keyword in ("藪", "やぶ", "砂場", "更科", "翁", "達磨", "室町", "並木")):
            add_tag(tags, "mood.traditional", 0.66, 0.66, "name_keyword", "classic_soba_lineage")

    for signal in (external_signal_index or {}).get(restaurant["url"], []):
        key = signal.get("key")
        if key not in TAG_DEFINITIONS:
            continue
        evidence_terms = []
        for value in signal.get("evidence") or []:
            if isinstance(value, str) and value.startswith("term:"):
                evidence_terms.append(value.replace("term:", "", 1))
        source_types = [value for value in signal.get("sourceTypes") or [] if isinstance(value, str)]
        evidence = "external"
        if source_types:
            evidence += f":{','.join(sorted(source_types))}"
        if evidence_terms:
            evidence += f":{','.join(sorted(evidence_terms)[:3])}"
        add_tag(
            tags,
            key,
            float(signal.get("weight", 0)),
            float(signal.get("confidence", 0)),
            "external_signal",
            evidence,
        )

    return sorted(tags.values(), key=lambda item: (item["key"], item["source"]))


def load_restaurants() -> list[dict[str, Any]]:
    restaurants: list[dict[str, Any]] = []
    for path in DATASETS:
        restaurants.extend(json.loads(path.read_text(encoding="utf-8")))
    return restaurants


def data_version_payload() -> dict[str, Any]:
    if DATA_VERSION.exists():
        return json.loads(DATA_VERSION.read_text(encoding="utf-8"))
    return {"version": 1, "generatedAt": None, "datasets": {}}


def external_signal_index() -> dict[str, list[dict[str, Any]]]:
    if not EXTERNAL_SIGNALS.exists():
        return {}
    payload = json.loads(EXTERNAL_SIGNALS.read_text(encoding="utf-8"))
    result: dict[str, list[dict[str, Any]]] = {}
    for item in payload.get("restaurants") or []:
        url = item.get("url")
        signals = item.get("signals")
        if isinstance(url, str) and isinstance(signals, list):
            result[url] = [signal for signal in signals if isinstance(signal, dict)]
    return result


def main() -> int:
    restaurants = load_restaurants()
    version = data_version_payload()
    ext_index = external_signal_index()
    affinity_groups = build_affinity_groups(restaurants)
    thresholds = {
        "udon": hall_of_fame_threshold(restaurants, "udon"),
        "soba": hall_of_fame_threshold(restaurants, "soba"),
    }
    dataset_hashes = {path.name: sha256(path) for path in DATASETS}

    for prefecture, slug in PREFECTURE_SLUGS.items():
        add_definition(f"pref.{slug}", prefecture, "fact")

    records = []
    for restaurant in restaurants:
        tags = build_tags_for_restaurant(restaurant, thresholds, ext_index)
        records.append(
            {
                "url": restaurant["url"],
                "name": restaurant["name"],
                "category": restaurant["category"],
                "tags": tags,
            }
        )

    payload = {
        "version": 1,
        "generatedAt": version.get("generatedAt"),
        "basedOn": {
            "dataVersionGeneratedAt": version.get("generatedAt"),
            "datasetSha256": dataset_hashes,
            "externalSignalsSha256": sha256(EXTERNAL_SIGNALS) if EXTERNAL_SIGNALS.exists() else None,
        },
        "method": {
            "summary": "Static recommendation tags generated from existing data, conservative rule-based priors, and deterministic external signal hints. Runtime recommendation can use these tags without calling an LLM or external API.",
            "confidencePolicy": {
                "1.0": "Existing dataset fact",
                "0.75-0.90": "Direct shop-name keyword or strong regional specialty prior",
                "0.60-0.74": "Selection-history or category-specific regional prior",
                "0.45-0.59": "Weak category or station-area prior; suitable for scoring, not strong display copy",
            },
            "externalSignalPolicy": "External signals are short manually reviewed evidence terms mapped to existing tags. Raw external page text, reviews, ratings, photos, and social posts are not stored.",
            "displayPolicy": "Inferred tags are exploration hints, not factual claims. Avoid displaying low-confidence inferred tags as definitive descriptions.",
        },
        "thresholds": {
            "hallOfFameSelectionCount": thresholds,
            "minimumConfidenceToOutput": MIN_CONFIDENCE_TO_OUTPUT,
        },
        "tagDefinitions": dict(sorted(TAG_DEFINITIONS.items())),
        "affinityGroups": affinity_groups,
        "restaurants": records,
    }

    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    total_tags = sum(len(record["tags"]) for record in records)
    inferred_tags = sum(1 for record in records for tag in record["tags"] if tag["source"] != "data")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")
    print(f"restaurants={len(records)} tags={total_tags} inferred_tags={inferred_tags}")
    print(f"affinity_groups={len(affinity_groups)}")
    print(f"hall_of_fame_thresholds={thresholds}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
