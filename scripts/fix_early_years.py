"""
2017-2019年度データの修正スクリプト
- 旧デザインのページではhyakumeiten-shop__targetクラスが存在しない
- tabelog.comへのリンクURLから店舗を抽出する
- 既存のrestaurants.jsonに年度情報をマージする
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
]

def fetch_page(url, retries=2):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'text/html',
        'Accept-Language': 'ja,en;q=0.5',
    }
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.read().decode('utf-8', errors='replace')
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


def parse_stores_old_design(html):
    """
    旧デザイン（2017-2019）のHTMLから店舗URLを抽出。
    パターン: tabelog.comの個別店舗ページURLをユニークに収集。
    店舗URLの形式: https://tabelog.com/{prefecture}/{area}/{subarea}/{id}/
    ナビゲーション用リンク等を除外するため、パスが4セグメント以上のものだけ抽出。
    """
    # tabelog.comの店舗URLを抽出（4セグメント以上 = 個別店舗ページ）
    url_pattern = re.compile(
        r'href="(https://tabelog\.com/[a-z]+/A\d+/A\d+/\d+/?)"'
    )
    
    urls = set()
    for match in url_pattern.finditer(html):
        url = match.group(1).strip().rstrip('/')
        urls.add(url)
    
    return list(urls)


def normalize_url(url):
    url = url.strip().rstrip('/')
    url = re.sub(r'^http://', 'https://', url)
    return url


def main():
    data_path = "/Users/miitarou/Documents/New project/data/restaurants.json"
    
    with open(data_path, 'r', encoding='utf-8') as f:
        restaurants = json.load(f)
    
    print("=== 2017-2019年度データ修正 ===")
    print(f"既存データ: {len(restaurants)} 店舗")
    
    # 既存データをURLでインデックス
    url_index = {}
    for r in restaurants:
        nurl = normalize_url(r['url'])
        url_index[nurl] = r
    
    # 現在の年度分布
    year_counts_before = {}
    for r in restaurants:
        for y in r.get('years', []):
            year_counts_before[y] = year_counts_before.get(y, 0) + 1
    print(f"修正前の年度分布: {dict(sorted(year_counts_before.items()))}")
    
    # 2017-2019のデータ収集
    year_urls = {}  # {year: [urls]}
    
    for target in TARGETS:
        year, url = target["year"], target["url"]
        print(f"\n📄 {year}年 取得中...", end=" ", flush=True)
        time.sleep(2)
        
        html = fetch_page(url)
        if not html:
            print("❌ 取得失敗")
            continue
        
        store_urls = parse_stores_old_design(html)
        print(f"✅ {len(store_urls)} 店舗URL抽出")
        year_urls[year] = store_urls
        
        # サンプル表示
        for u in store_urls[:3]:
            print(f"   - {u}")
    
    # 既存データに年度を追記
    matched = 0
    unmatched_urls = []
    
    for year, urls in year_urls.items():
        print(f"\n=== {year}年のマッチング ===")
        year_matched = 0
        year_unmatched = []
        
        for url in urls:
            nurl = normalize_url(url)
            if nurl in url_index:
                r = url_index[nurl]
                if 'years' not in r or not isinstance(r['years'], list):
                    r['years'] = []
                if year not in r['years']:
                    r['years'].append(year)
                    r['years'].sort()
                year_matched += 1
            else:
                year_unmatched.append(nurl)
        
        matched += year_matched
        unmatched_urls.extend([(year, u) for u in year_unmatched])
        print(f"  マッチ: {year_matched}")
        print(f"  未マッチ: {len(year_unmatched)}")
    
    # 未マッチの店舗情報（既存データにない過去の店舗）
    if unmatched_urls:
        print(f"\n=== 未マッチ店舗（{len(unmatched_urls)}件）===")
        # 未マッチ店舗を新規追加（座標なし）
        added = 0
        for year, url in unmatched_urls:
            if url not in url_index:
                new_entry = {
                    "name": url.split('/')[-1] if url.split('/')[-1] else "不明",
                    "url": url,
                    "region": "EAST",  # 統合版なので暫定
                    "area": "",
                    "prefecture": "",
                    "holiday": "",
                    "firstSelected": False,
                    "closed": False,
                    "lat": None,
                    "lng": None,
                    "years": [year],
                }
                restaurants.append(new_entry)
                url_index[url] = new_entry
                added += 1
                print(f"  + [{year}] {url}")
        print(f"  新規追加: {added}")
    
    # 修正後の年度分布
    year_counts_after = {}
    for r in restaurants:
        for y in r.get('years', []):
            year_counts_after[y] = year_counts_after.get(y, 0) + 1
    print(f"\n修正後の年度分布: {dict(sorted(year_counts_after.items()))}")
    
    # 保存
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(restaurants, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 保存完了: {data_path}")
    print(f"合計: {len(restaurants)} 店舗")


if __name__ == "__main__":
    main()
