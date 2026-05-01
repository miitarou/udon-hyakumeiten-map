"""
BUG-005対応（修正版）: 食べログの個別店舗ページからJSON-LD構造化データで住所を抽出
addressRegion（都道府県） + addressLocality（市区） + streetAddress（番地）
"""
import json
import time
import re
import urllib.request
import urllib.error

DATA_PATH = "/Users/miitarou/Documents/New project/data/restaurants.json"
OUTPUT_PATH = "/Users/miitarou/Documents/New project/data/restaurants.json"
PROGRESS_PATH = "/Users/miitarou/Documents/New project/data/address_progress.json"

def fetch_page(url, retries=3):
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
                wait = 20 * (attempt + 1)
                print(f"  ⚠ 429 Rate Limited, {wait}秒待機...")
                time.sleep(wait)
            elif attempt < retries - 1:
                time.sleep(5)
            else:
                print(f"  ⚠ HTTP {e.code}")
                return None
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(5)
            else:
                print(f"  ⚠ {e}")
                return None
    return None


def extract_address_from_jsonld(html):
    """JSON-LD構造化データから住所を抽出"""
    # "addressRegion":"東京都","addressLocality":"中央区","streetAddress":"日本橋人形町2-15-17"
    region_match = re.search(r'"addressRegion"\s*:\s*"([^"]+)"', html)
    locality_match = re.search(r'"addressLocality"\s*:\s*"([^"]+)"', html)
    street_match = re.search(r'"streetAddress"\s*:\s*"([^"]+)"', html)
    
    parts = []
    if region_match:
        parts.append(region_match.group(1))
    if locality_match:
        parts.append(locality_match.group(1))
    if street_match:
        parts.append(street_match.group(1))
    
    if parts:
        return ''.join(parts)
    return None


def main():
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        restaurants = json.load(f)
    
    # 進捗読み込み
    try:
        with open(PROGRESS_PATH, 'r', encoding='utf-8') as f:
            progress = json.load(f)
    except FileNotFoundError:
        progress = {}
    
    need_address = [r for r in restaurants if not r.get('address') and r.get('url')]
    print(f"=== 住所取得（JSON-LD版） ===")
    print(f"全店舗: {len(restaurants)}")
    print(f"住所未取得: {len(need_address)}")
    print(f"キャッシュ済: {len(progress)}")
    
    updated = 0
    failed = 0
    cache_hit = 0
    
    for i, r in enumerate(need_address):
        url = r['url']
        
        # キャッシュから復元
        if url in progress:
            addr = progress[url]
            if addr:
                r['address'] = addr
                updated += 1
            cache_hit += 1
            continue
        
        print(f"  [{i+1}/{len(need_address)}] {r.get('name', '?')}...", end=" ", flush=True)
        
        html = fetch_page(url)
        if not html:
            print("❌ 取得失敗")
            progress[url] = None
            failed += 1
        else:
            addr = extract_address_from_jsonld(html)
            if addr:
                r['address'] = addr
                progress[url] = addr
                updated += 1
                print(f"✅ {addr}")
            else:
                progress[url] = None
                failed += 1
                print("⚠ 抽出失敗")
        
        # 20件ごとに中間保存
        if (i + 1 - cache_hit) % 20 == 0:
            with open(PROGRESS_PATH, 'w', encoding='utf-8') as f:
                json.dump(progress, f, ensure_ascii=False)
            with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
                json.dump(restaurants, f, ensure_ascii=False, indent=2)
            print(f"  💾 中間保存 ({updated}件更新)")
        
        # レート制限対策（1.5秒間隔）
        time.sleep(1.5)
    
    # 最終保存
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(restaurants, f, ensure_ascii=False, indent=2)
    with open(PROGRESS_PATH, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False)
    
    total_with_addr = sum(1 for r in restaurants if r.get('address'))
    print(f"\n=== 結果 ===")
    print(f"住所取得成功: {updated}")
    print(f"取得失敗: {failed}")
    print(f"キャッシュ: {cache_hit}")
    print(f"住所あり合計: {total_with_addr}/{len(restaurants)}")


if __name__ == "__main__":
    main()
