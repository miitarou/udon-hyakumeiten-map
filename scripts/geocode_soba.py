"""
そば百名店 ジオコーディングスクリプト
data/soba_raw.json を読み込み、Nominatim API で座標を付与して data/soba.json を生成する。

注意:
  Nominatimの利用ポリシー（https://operations.osmfoundation.org/policies/nominatim/）に従い、
  リクエスト間隔は 1.1 秒以上あけてください。
  本スクリプトは一度限りの実行を想定しています。

実行方法:
  cd <repo-root>
  python3 scripts/geocode_soba.py
"""
import json
import time
import random
import urllib.request
import urllib.parse
from pathlib import Path

# ジオコーディング共通関数（geocode_restaurants.py と同じ）
def geocode_nominatim(query, retries=2):
    encoded = urllib.parse.quote(query)
    url = f"https://nominatim.openstreetmap.org/search?q={encoded}&format=json&limit=1&countrycodes=jp"
    headers = {'User-Agent': 'SobaMapProject/1.0 (personal use)'}
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                if data:
                    return float(data[0]['lat']), float(data[0]['lon'])
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2)
            else:
                print(f"  ⚠ ジオコーディング失敗: {query} - {e}")
    return None, None

# 都道府県デフォルト座標
PREF_DEFAULT = {
    "北海道": (43.0618, 141.3545), "青森県": (40.8244, 140.7400), "岩手県": (39.7036, 141.1527),
    "宮城県": (38.2688, 140.8721), "秋田県": (39.7186, 140.1024), "山形県": (38.2404, 140.3634),
    "福島県": (37.7503, 140.4676), "茨城県": (36.3419, 140.4468), "栃木県": (36.5665, 139.8836),
    "群馬県": (36.3911, 139.0608), "埼玉県": (35.8567, 139.6489), "千葉県": (35.6050, 140.1233),
    "東京都": (35.6762, 139.6503), "神奈川県": (35.4476, 139.6425), "新潟県": (37.9022, 139.0234),
    "富山県": (36.6953, 137.2113), "石川県": (36.5946, 136.6256), "福井県": (36.0653, 136.2217),
    "山梨県": (35.6639, 138.5684), "長野県": (36.2320, 138.1811), "岐阜県": (35.3912, 136.7224),
    "静岡県": (34.9756, 138.3828), "愛知県": (35.1802, 136.9066), "三重県": (34.7303, 136.5086),
    "滋賀県": (35.0045, 135.8686), "京都府": (35.0116, 135.7681), "大阪府": (34.6864, 135.5200),
    "兵庫県": (34.6913, 135.1830), "奈良県": (34.6851, 135.8328), "和歌山県": (34.2261, 135.1675),
    "鳥取県": (35.5039, 134.2380), "島根県": (35.4723, 133.0505), "岡山県": (34.6617, 133.9348),
    "広島県": (34.3966, 132.4596), "山口県": (34.1860, 131.4715), "徳島県": (34.0658, 134.5593),
    "香川県": (34.3401, 134.0434), "愛媛県": (33.8416, 132.7660), "高知県": (33.5597, 133.5311),
    "福岡県": (33.6064, 130.4183), "佐賀県": (33.2494, 130.2988), "長崎県": (32.7503, 129.8779),
    "熊本県": (32.7898, 130.7417), "大分県": (33.2382, 131.6126), "宮崎県": (31.9111, 131.4239),
    "鹿児島県": (31.5602, 130.5581), "沖縄県": (26.2124, 127.6809),
}


def main():
    base_dir = Path(__file__).resolve().parents[1]
    input_path = base_dir / "data" / "soba_raw.json"
    output_path = base_dir / "data" / "soba.json"

    with open(input_path, 'r', encoding='utf-8') as f:
        stores = json.load(f)

    print(f"入力: {len(stores)} 店舗")

    geocoded = failed = skipped = 0

    for i, r in enumerate(stores):
        if r.get('lat') is not None and r.get('lng') is not None:
            skipped += 1
            continue

        area = r.get('area', '')
        prefecture = r.get('prefecture', '')

        query = f"{area}, {prefecture}, Japan"
        time.sleep(1.1)
        lat, lng = geocode_nominatim(query)

        if lat is not None:
            r['lat'] = lat
            r['lng'] = lng
            geocoded += 1
            print(f"  [{i+1}/{len(stores)}] ✅ {r['name']} → ({lat:.4f}, {lng:.4f})")
        else:
            if prefecture in PREF_DEFAULT:
                base_lat, base_lng = PREF_DEFAULT[prefecture]
                r['lat'] = base_lat + random.uniform(-0.015, 0.015)
                r['lng'] = base_lng + random.uniform(-0.015, 0.015)
                print(f"  [{i+1}/{len(stores)}] ⚠ {r['name']} → 都道府県デフォルト ({r['lat']:.4f}, {r['lng']:.4f})")
                geocoded += 1
            else:
                failed += 1
                print(f"  [{i+1}/{len(stores)}] ❌ {r['name']} → 失敗")

    print(f"\n=== ジオコーディング結果 ===")
    print(f"  成功: {geocoded}, スキップ: {skipped}, 失敗: {failed}")

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(stores, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 出力完了: {output_path} ({len(stores)} 店舗)")


if __name__ == "__main__":
    main()
