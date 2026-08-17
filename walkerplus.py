"""WalkerPlus イベント情報スクレイピングモジュール。"""

from __future__ import annotations

from datetime import datetime
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.walkerplus.com"
USER_AGENT = "Mozilla/5.0 (compatible; hanabi_bot/1.0; event search bot)"
MAX_EVENTS = 5

# ISO3166-2 (日本) -> WalkerPlus エリアコード
ISO3166_2_TO_AREA_CODE = {
    "JP-01": "ar0101",
    "JP-02": "ar0202",
    "JP-03": "ar0203",
    "JP-04": "ar0204",
    "JP-05": "ar0205",
    "JP-06": "ar0206",
    "JP-07": "ar0207",
    "JP-08": "ar0308",
    "JP-09": "ar0309",
    "JP-10": "ar0310",
    "JP-11": "ar0311",
    "JP-12": "ar0312",
    "JP-13": "ar0313",
    "JP-14": "ar0314",
    "JP-15": "ar0415",
    "JP-16": "ar0516",
    "JP-17": "ar0517",
    "JP-18": "ar0518",
    "JP-19": "ar0419",
    "JP-20": "ar0420",
    "JP-21": "ar0621",
    "JP-22": "ar0622",
    "JP-23": "ar0623",
    "JP-24": "ar0624",
    "JP-25": "ar0725",
    "JP-26": "ar0726",
    "JP-27": "ar0727",
    "JP-28": "ar0728",
    "JP-29": "ar0729",
    "JP-30": "ar0730",
    "JP-31": "ar0831",
    "JP-32": "ar0832",
    "JP-33": "ar0833",
    "JP-34": "ar0834",
    "JP-35": "ar0835",
    "JP-36": "ar0936",
    "JP-37": "ar0937",
    "JP-38": "ar0938",
    "JP-39": "ar0939",
    "JP-40": "ar1040",
    "JP-41": "ar1041",
    "JP-42": "ar1042",
    "JP-43": "ar1043",
    "JP-44": "ar1044",
    "JP-45": "ar1045",
    "JP-46": "ar1046",
    "JP-47": "ar1047",
}

# 都道府県名 -> WalkerPlus エリアコード
# サイト構造変更時は /info/search/event/ のエリアリンクを再確認すること。
PREFECTURE_TO_AREA_CODE = {
    "北海道": "ar0101",
    "青森県": "ar0202",
    "岩手県": "ar0203",
    "宮城県": "ar0204",
    "秋田県": "ar0205",
    "山形県": "ar0206",
    "福島県": "ar0207",
    "茨城県": "ar0308",
    "栃木県": "ar0309",
    "群馬県": "ar0310",
    "埼玉県": "ar0311",
    "千葉県": "ar0312",
    "東京都": "ar0313",
    "神奈川県": "ar0314",
    "新潟県": "ar0415",
    "山梨県": "ar0419",
    "長野県": "ar0420",
    "富山県": "ar0516",
    "石川県": "ar0517",
    "福井県": "ar0518",
    "岐阜県": "ar0621",
    "静岡県": "ar0622",
    "愛知県": "ar0623",
    "三重県": "ar0624",
    "滋賀県": "ar0725",
    "京都府": "ar0726",
    "大阪府": "ar0727",
    "兵庫県": "ar0728",
    "奈良県": "ar0729",
    "和歌山県": "ar0730",
    "鳥取県": "ar0831",
    "島根県": "ar0832",
    "岡山県": "ar0833",
    "広島県": "ar0834",
    "山口県": "ar0835",
    "徳島県": "ar0936",
    "香川県": "ar0937",
    "愛媛県": "ar0938",
    "高知県": "ar0939",
    "福岡県": "ar1040",
    "佐賀県": "ar1041",
    "長崎県": "ar1042",
    "熊本県": "ar1043",
    "大分県": "ar1044",
    "宮崎県": "ar1045",
    "鹿児島県": "ar1046",
    "沖縄県": "ar1047",
}


def build_search_url(latitude: float, longitude: float, date_str: str) -> str:
    """緯度・経度・日付から WalkerPlus のイベント一覧 URL を組み立てる。"""
    area_code = _latitude_longitude_to_area_code(latitude, longitude)
    date_part = datetime.strptime(date_str, "%Y-%m-%d").strftime("%m%d")
    return f"{BASE_URL}/event_list/{date_part}/{area_code}/"


def scrape_walkerplus(
    latitude: float, longitude: float, date_str: str
) -> list[dict[str, str]]:
    """
    WalkerPlus からイベント情報を取得する。

    注意: 対象サイトの HTML 構造は予告なく変更される可能性があります。
    取得に失敗した場合は、CSS セレクタや URL 形式の見直しが必要です。
    """
    search_url = build_search_url(latitude, longitude, date_str)
    response = requests.get(
        search_url,
        headers={"User-Agent": USER_AGENT},
        timeout=10,
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    events: list[dict[str, str]] = []

    # イベント一覧の DOM 構造に依存しているため、サイト改修で要メンテナンス。
    for item in soup.select(".m-mainlist-item"):
        title_element = item.select_one(".m-mainlist-item__ttl")
        link_element = item.select_one("a[href*='/event/']")
        image_element = item.select_one(".m-mainlist-item__img img")

        if not title_element or not link_element:
            continue

        title = title_element.get_text(strip=True)
        link_url = urljoin(BASE_URL, link_element["href"])

        image_url = ""
        if image_element:
            raw_image_url = (
                image_element.get("src")
                or image_element.get("data-src")
                or image_element.get("data-original")
                or ""
            )
            image_url = urljoin(BASE_URL, raw_image_url)

        events.append(
            {
                "title": title,
                "image_url": image_url,
                "link_url": link_url,
            }
        )

        if len(events) >= MAX_EVENTS:
            break

    return events


def _latitude_longitude_to_area_code(latitude: float, longitude: float) -> str:
    """緯度・経度から WalkerPlus のエリアコードを推定する。"""
    response = requests.get(
        "https://nominatim.openstreetmap.org/reverse",
        params={
            "lat": latitude,
            "lon": longitude,
            "format": "json",
            "accept-language": "ja",
        },
        headers={"User-Agent": USER_AGENT},
        timeout=10,
    )
    response.raise_for_status()

    address = response.json().get("address", {})

    iso_code = address.get("ISO3166-2-lvl4")
    if iso_code in ISO3166_2_TO_AREA_CODE:
        return ISO3166_2_TO_AREA_CODE[iso_code]

    prefecture = (
        address.get("province")
        or address.get("state")
        or address.get("region")
        or ""
    )

    area_code = PREFECTURE_TO_AREA_CODE.get(prefecture)
    if area_code:
        return area_code

    # 都道府県が特定できない場合は関東全体をフォールバックとする。
    return "ar0300"
