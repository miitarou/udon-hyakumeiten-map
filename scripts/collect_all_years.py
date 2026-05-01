"""
食べログ うどん百名店 全年度データ収集（修正版）
- HTMLから <img alt="店名"> パターンで店舗名を抽出
- 全年度を統合して名寄せ
"""
import json
import time
import re
import urllib.request
import urllib.error

TARGETS = [
    {"year": 2017, "region": "ALL", "url": "https://award.tabelog.com/hyakumeiten/udon/2017"},
    {"year": 2018, "region": "ALL", "url": "https://award.tabelog.com/hyakumeiten/udon/2018"},
    {"year": 2019, "region": "ALL", "url": "https://award.tabelog.com/hyakumeiten/udon/2019"},
    {"year": 2020, "region": "EAST",  "url": "https://award.tabelog.com/hyakumeiten/udon_east/2020"},
    {"year": 2020, "region": "WEST",  "url": "https://award.tabelog.com/hyakumeiten/udon_west/2020"},
    {"year": 2020, "region": "TOKYO", "url": "https://award.tabelog.com/hyakumeiten/udon_tokyo/2020"},
    {"year": 2022, "region": "EAST",  "url": "https://award.tabelog.com/hyakumeiten/udon_east/2022"},
    {"year": 2022, "region": "WEST",  "url": "https://award.tabelog.com/hyakumeiten/udon_west/2022"},
]

def fetch_page(url, retries=2):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'ja,en;q=0.5',
    }
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as response:
                return response.read().decode('utf-8', errors='replace')
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(10 * (attempt + 1))
            elif attempt < retries - 1:
                time.sleep(3)
            else:
                print(f"  ⚠ HTTP {e.code}")
        except Exception as e:
            print(f"  ⚠ {e}")
            if attempt < retries - 1:
                time.sleep(3)
    return None


def parse_stores(html):
    """
    百名店ページのHTML構造:
    <div class="hyakumeiten-shop__item">
      <a class="hyakumeiten-shop__target" href="https://tabelog.com/...">
        <div class="hyakumeiten-shop__img">
          <img alt="店名" ...>
    
    店舗URL + alt属性の店名をペアで抽出
    """
    results = []
    
    # hyakumeiten-shop__target リンクから URL と直後の img alt を抽出
    pattern = re.compile(
        r'hyakumeiten-shop__target[^"]*"[^>]*href="(https://tabelog\.com/[^"]+)"'
        r'[^>]*>.*?<img\s+alt="([^"]*)"',
        re.DOTALL
    )
    
    for match in pattern.finditer(html):
        url = match.group(1).strip().rstrip('/')
        name = match.group(2).strip()
        if name and len(name) >= 2:
            results.append({"name": name, "url": url})
    
    return results


def normalize_url(url):
    url = url.strip().rstrip('/')
    url = re.sub(r'^http://', 'https://', url)
    return url


def main():
    existing_path = "/Users/miitarou/Documents/New project/data/restaurants.json"
    output_path = "/Users/miitarou/Documents/New project/data/restaurants.json"  # 上書き

    with open(existing_path, 'r', encoding='utf-8') as f:
        existing = json.load(f)

    print("=== 食べログ うどん百名店 全年度データ収集（修正版） ===")
    print(f"既存データ: {len(existing)} 店舗\n")

    # 全年度のデータを収集
    year_records = []  # (url, name, year, region)

    for target in TARGETS:
        year, region, url = target["year"], target["region"], target["url"]
        print(f"📄 {year}年 {region}...", end=" ", flush=True)
        time.sleep(2)

        html = fetch_page(url)
        if not html:
            print("❌ 取得失敗")
            continue

        stores = parse_stores(html)
        print(f"✅ {len(stores)} 店舗")
        for s in stores[:2]:
            print(f"   - {s['name']}")

        for s in stores:
            year_records.append({
                "url": normalize_url(s["url"]),
                "name": s["name"],
                "year": year,
                "region": region,
            })

    # 2024年のデータを追加
    for r in existing:
        year_records.append({
            "url": normalize_url(r["url"]),
            "name": r["name"],
            "year": 2024,
            "region": r.get("region", "EAST"),
        })

    # === 名寄せ: URLで統合 ===
    print(f"\n=== 名寄せ ===")
    store_map = {}
    for rec in year_records:
        url = rec["url"]
        if url not in store_map:
            store_map[url] = {
                "name": rec["name"],
                "years": set(),
                "regions": set(),
            }
        store_map[url]["years"].add(rec["year"])
        store_map[url]["regions"].add(rec["region"])
        # 2024年の名前を優先
        if rec["year"] == 2024:
            store_map[url]["name"] = rec["name"]

    print(f"ユニーク店舗数: {len(store_map)}")

    # 年度別統計
    year_counts = {}
    for info in store_map.values():
        for y in info["years"]:
            year_counts[y] = year_counts.get(y, 0) + 1
    for y in sorted(year_counts):
        print(f"  {y}年: {year_counts[y]} 店舗")

    # 複数年選出
    multi = [(url, info) for url, info in store_map.items() if len(info["years"]) > 1]
    print(f"\n複数年選出: {len(multi)} 店舗")
    for url, info in sorted(multi, key=lambda x: -len(x[1]["years"]))[:10]:
        ys = ", ".join(str(y) for y in sorted(info["years"]))
        print(f"  {info['name']}: {ys}")

    # === 既存データにyearsを追加 & 新規店舗を追加 ===
    existing_by_url = {}
    for r in existing:
        url = normalize_url(r["url"])
        existing_by_url[url] = r

    new_stores = []
    for url, info in store_map.items():
        years_sorted = sorted(info["years"])
        if url in existing_by_url:
            existing_by_url[url]["years"] = years_sorted
        else:
            # 新規店舗（過去年度のみ）
            regions = info["regions"]
            if "EAST" in regions or "TOKYO" in regions:
                region = "EAST"
            elif "WEST" in regions:
                region = "WEST"
            else:
                region = "EAST"  # ALL=統合版は地域不明、EASTとする

            new_stores.append({
                "name": info["name"],
                "url": url,
                "region": region,
                "area": "",
                "prefecture": "",
                "holiday": "",
                "is_first_selected": False,
                "is_closed": False,
                "lat": None,
                "lng": None,
                "years": years_sorted,
            })

    # 2024年のみの店にもyears追加
    for url, r in existing_by_url.items():
        if "years" not in r:
            r["years"] = [2024]

    updated = list(existing_by_url.values()) + new_stores

    print(f"\n=== 結果 ===")
    print(f"既存更新: {len(existing_by_url)}")
    print(f"新規追加: {len(new_stores)}")
    print(f"合計: {len(updated)}")

    # 保存
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(updated, f, ensure_ascii=False, indent=2)
    print(f"保存: {output_path}")

    # 新規店舗一覧
    if new_stores:
        print(f"\n新規店舗（座標未取得）:")
        for s in new_stores:
            ys = ", ".join(str(y) for y in s["years"])
            print(f"  {s['name']} ({ys}) {s['url']}")


if __name__ == "__main__":
    main()
