"""
BUG-005対応: 住所検索の改善
- restaurants.jsonの各店舗に住所情報(address)が不足
- 食べログURLから住所を取得して補完する
- まず現在のareaフィールドの内容を分析する
"""
import json

data_path = "/Users/miitarou/Documents/New project/data/restaurants.json"

with open(data_path, 'r', encoding='utf-8') as f:
    restaurants = json.load(f)

# area フィールドの分析
area_samples = {}
for r in restaurants:
    area = r.get('area', '')
    if '駅' in area:
        area_samples.setdefault('駅名', []).append(area)
    elif '市' in area or '区' in area or '町' in area or '村' in area:
        area_samples.setdefault('市区町村', []).append(area)
    elif area:
        area_samples.setdefault('その他', []).append(area)
    else:
        area_samples.setdefault('空', []).append(r.get('name', ''))

print("=== area フィールド分析 ===")
for cat, items in area_samples.items():
    print(f"  {cat}: {len(items)} 件")
    for item in items[:5]:
        print(f"    - {item}")

# 「豊中市」で検索したい場合の問題
# areaが「豊中駅」などの駅名の場合、「豊中市」ではヒットしない
# 解決策: URLの都道府県から推定するか、手動で住所を入れるか

print("\n=== 「豊中」を含むデータ ===")
for r in restaurants:
    if '豊中' in (r.get('area', '') + r.get('prefecture', '') + r.get('name', '')):
        print(f"  {r['name']} | area: {r.get('area')} | pref: {r.get('prefecture')}")
    
# 大阪府の店舗でareaに「豊中」が含まれないケース
print("\n=== 大阪府の全area ===")
osaka = [r for r in restaurants if r.get('prefecture') == '大阪府']
for r in osaka:
    print(f"  {r['name']}: area={r.get('area')}")
