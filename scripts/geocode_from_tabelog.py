"""
食べログページから正確な緯度経度を取得するスクリプト
- 各店舗のURLからHTMLを取得
- __NEXT_DATA__ JSON または meta タグから lat/lng を抽出
- レート制限: 2秒/リクエスト（食べログに配慮）
"""
import json
import time
import re
import urllib.request
import urllib.error
import sys

def fetch_page(url, retries=2):
    """URLからHTMLを取得"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'ja,en;q=0.5',
    }
    
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as response:
                return response.read().decode('utf-8', errors='replace')
        except urllib.error.HTTPError as e:
            if e.code == 429:  # Rate limited
                wait = 10 * (attempt + 1)
                print(f"  ⏳ レート制限。{wait}秒待機...")
                time.sleep(wait)
            elif e.code == 403:
                print(f"  🚫 アクセス拒否 (403)")
                return None
            else:
                print(f"  ⚠ HTTP {e.code}")
                if attempt < retries - 1:
                    time.sleep(3)
        except Exception as e:
            print(f"  ⚠ エラー: {e}")
            if attempt < retries - 1:
                time.sleep(3)
    return None


def extract_coords_from_html(html):
    """HTMLから緯度経度を抽出する（複数の方法を試行）"""
    
    # 方法1: __NEXT_DATA__ の JSON から取得
    next_data_match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
    if next_data_match:
        try:
            data = json.loads(next_data_match.group(1))
            # ネストされたJSONを再帰的に検索
            coords = find_coords_in_dict(data)
            if coords:
                return coords
        except json.JSONDecodeError:
            pass
    
    # 方法2: script内の lat/lng パターンを検索
    # 食べログは地図表示用に座標をJSに埋め込んでいることが多い
    patterns = [
        # "lat":35.1234,"lng":136.5678 形式
        r'"lat"\s*:\s*([0-9]+\.[0-9]+)\s*,\s*"lng"\s*:\s*([0-9]+\.[0-9]+)',
        r'"latitude"\s*:\s*([0-9]+\.[0-9]+)\s*,\s*"longitude"\s*:\s*([0-9]+\.[0-9]+)',
        # lat=35.1234&lng=136.5678 形式
        r'lat=([0-9]+\.[0-9]+)&(?:amp;)?lng=([0-9]+\.[0-9]+)',
        r'latitude=([0-9]+\.[0-9]+)&(?:amp;)?longitude=([0-9]+\.[0-9]+)',
        # LatLng(35.1234, 136.5678) 形式
        r'LatLng\(\s*([0-9]+\.[0-9]+)\s*,\s*([0-9]+\.[0-9]+)\s*\)',
        # data-lat="35.1234" data-lng="136.5678" 形式
        r'data-lat="([0-9]+\.[0-9]+)"[^>]*data-lng="([0-9]+\.[0-9]+)"',
        r'data-lng="([0-9]+\.[0-9]+)"[^>]*data-lat="([0-9]+\.[0-9]+)"',
        # center: [35.1234, 136.5678]
        r'center\s*:\s*\[\s*([0-9]+\.[0-9]+)\s*,\s*([0-9]+\.[0-9]+)\s*\]',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, html)
        if match:
            lat, lng = float(match.group(1)), float(match.group(2))
            # 日本の座標範囲チェック
            if 24 <= lat <= 46 and 122 <= lng <= 154:
                return (lat, lng)
            # lat/lngが逆の可能性
            if 24 <= lng <= 46 and 122 <= lat <= 154:
                return (lng, lat)
    
    # 方法3: meta タグから取得
    geo_patterns = [
        r'<meta[^>]*property="place:location:latitude"[^>]*content="([0-9]+\.[0-9]+)"',
        r'<meta[^>]*property="place:location:longitude"[^>]*content="([0-9]+\.[0-9]+)"',
    ]
    
    lat_match = re.search(geo_patterns[0], html)
    lng_match = re.search(geo_patterns[1], html)
    if lat_match and lng_match:
        return (float(lat_match.group(1)), float(lng_match.group(1)))
    
    # 方法4: Google Maps URL から取得
    gmap_match = re.search(r'maps\.google\.[a-z]+/maps\?[^"]*ll=([0-9]+\.[0-9]+),([0-9]+\.[0-9]+)', html)
    if gmap_match:
        return (float(gmap_match.group(1)), float(gmap_match.group(2)))
    
    return None


def find_coords_in_dict(obj, depth=0):
    """辞書/リストを再帰的に探索して座標を見つける"""
    if depth > 10:
        return None
    
    if isinstance(obj, dict):
        # lat/lng キーの直接チェック
        lat = obj.get('lat') or obj.get('latitude')
        lng = obj.get('lng') or obj.get('longitude') or obj.get('lon')
        
        if lat and lng:
            try:
                lat_f, lng_f = float(lat), float(lng)
                if 24 <= lat_f <= 46 and 122 <= lng_f <= 154:
                    return (lat_f, lng_f)
            except (ValueError, TypeError):
                pass
        
        for v in obj.values():
            result = find_coords_in_dict(v, depth + 1)
            if result:
                return result
    
    elif isinstance(obj, list):
        for item in obj:
            result = find_coords_in_dict(item, depth + 1)
            if result:
                return result
    
    return None


def main():
    input_path = "/Users/miitarou/Documents/New project/data/restaurants.json"
    output_path = "/Users/miitarou/Documents/New project/data/restaurants.json"
    
    with open(input_path, 'r', encoding='utf-8') as f:
        restaurants = json.load(f)
    
    total = len(restaurants)
    updated = 0
    failed = 0
    skipped = 0
    
    print(f"=== 食べログから正確な座標を取得 ===")
    print(f"対象: {total} 店舗\n")
    
    for i, r in enumerate(restaurants):
        name = r['name']
        url = r['url']
        
        print(f"[{i+1}/{total}] {name}...", end=" ", flush=True)
        
        # レート制限: 2秒間隔
        if i > 0:
            time.sleep(2)
        
        html = fetch_page(url)
        if not html:
            print("❌ ページ取得失敗")
            failed += 1
            continue
        
        coords = extract_coords_from_html(html)
        if coords:
            old_lat, old_lng = r.get('lat'), r.get('lng')
            r['lat'], r['lng'] = coords[0], coords[1]
            
            # 変化量を計算
            if old_lat and old_lng:
                diff = abs(coords[0] - old_lat) + abs(coords[1] - old_lng)
                diff_label = f"(Δ{diff:.4f})" if diff > 0.001 else "(変化なし)"
            else:
                diff_label = "(新規)"
            
            print(f"✅ ({coords[0]:.6f}, {coords[1]:.6f}) {diff_label}")
            updated += 1
        else:
            print("⚠ 座標抽出失敗（既存値を維持）")
            skipped += 1
        
        # 進捗セーブ（10件ごと）
        if (i + 1) % 10 == 0:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(restaurants, f, ensure_ascii=False, indent=2)
            print(f"  💾 中間セーブ ({i+1}/{total})")
    
    # 最終保存
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(restaurants, f, ensure_ascii=False, indent=2)
    
    print(f"\n=== 完了 ===")
    print(f"  更新: {updated}")
    print(f"  抽出失敗: {skipped}")
    print(f"  取得失敗: {failed}")
    print(f"  出力: {output_path}")


if __name__ == "__main__":
    main()
