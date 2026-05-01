"""
座標未取得の店舗のみ食べログから座標を取得するスクリプト
"""
import json
import time
import re
import urllib.request
import urllib.error

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
            elif e.code in (403, 404):
                return None
            elif attempt < retries - 1:
                time.sleep(3)
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(3)
    return None

def extract_coords(html):
    patterns = [
        r'"lat"\s*:\s*([0-9]+\.[0-9]+)\s*,\s*"lng"\s*:\s*([0-9]+\.[0-9]+)',
        r'"latitude"\s*:\s*([0-9]+\.[0-9]+)\s*,\s*"longitude"\s*:\s*([0-9]+\.[0-9]+)',
        r'lat=([0-9]+\.[0-9]+)&(?:amp;)?lng=([0-9]+\.[0-9]+)',
        r'LatLng\(\s*([0-9]+\.[0-9]+)\s*,\s*([0-9]+\.[0-9]+)\s*\)',
        r'data-lat="([0-9]+\.[0-9]+)"[^>]*data-lng="([0-9]+\.[0-9]+)"',
        r'center\s*:\s*\[\s*([0-9]+\.[0-9]+)\s*,\s*([0-9]+\.[0-9]+)\s*\]',
    ]
    for p in patterns:
        m = re.search(p, html)
        if m:
            lat, lng = float(m.group(1)), float(m.group(2))
            if 24 <= lat <= 46 and 122 <= lng <= 154:
                return (lat, lng)
            if 24 <= lng <= 46 and 122 <= lat <= 154:
                return (lng, lat)
    
    # __NEXT_DATA__ から再帰検索
    nd = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
    if nd:
        try:
            data = json.loads(nd.group(1))
            return find_coords(data)
        except:
            pass
    return None

def find_coords(obj, depth=0):
    if depth > 10:
        return None
    if isinstance(obj, dict):
        lat = obj.get('lat') or obj.get('latitude')
        lng = obj.get('lng') or obj.get('longitude') or obj.get('lon')
        if lat and lng:
            try:
                lf, lnf = float(lat), float(lng)
                if 24 <= lf <= 46 and 122 <= lnf <= 154:
                    return (lf, lnf)
            except:
                pass
        for v in obj.values():
            r = find_coords(v, depth+1)
            if r: return r
    elif isinstance(obj, list):
        for item in obj:
            r = find_coords(item, depth+1)
            if r: return r
    return None

def main():
    path = "/Users/miitarou/Documents/New project/data/restaurants.json"
    with open(path, 'r', encoding='utf-8') as f:
        restaurants = json.load(f)

    needs_geocode = [r for r in restaurants if not r.get('lat')]
    print(f"=== 座標未取得店舗のジオコーディング ===")
    print(f"対象: {len(needs_geocode)} / {len(restaurants)} 店舗\n")

    updated = 0
    failed = 0

    for i, r in enumerate(needs_geocode):
        print(f"[{i+1}/{len(needs_geocode)}] {r['name']}...", end=" ", flush=True)
        if i > 0:
            time.sleep(2)

        html = fetch_page(r['url'])
        if not html:
            print("❌ ページ取得失敗")
            failed += 1
            continue

        coords = extract_coords(html)
        if coords:
            r['lat'], r['lng'] = coords[0], coords[1]
            print(f"✅ ({coords[0]:.6f}, {coords[1]:.6f})")
            updated += 1
        else:
            print("⚠ 座標抽出失敗")
            failed += 1

        # 10件ごとにセーブ
        if (i+1) % 10 == 0:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(restaurants, f, ensure_ascii=False, indent=2)
            print(f"  💾 中間セーブ ({i+1}/{len(needs_geocode)})")

    # 最終保存
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(restaurants, f, ensure_ascii=False, indent=2)

    print(f"\n=== 完了 ===")
    print(f"  成功: {updated}")
    print(f"  失敗: {failed}")

if __name__ == "__main__":
    main()
