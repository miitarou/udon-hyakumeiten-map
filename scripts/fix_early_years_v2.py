"""
2017-2019年度データの修正 v2
- 旧ページのURLは県名・エリアコードが異なるため、店舗ID（末尾数字）でマッチング
- 既存データを一旦元に戻してから再マッチング
"""
import json
import re

def extract_store_id(url):
    """URLから店舗ID（末尾の数字部分）を抽出"""
    url = url.strip().rstrip('/')
    match = re.search(r'/(\d+)/?$', url)
    return match.group(1) if match else None

def main():
    data_path = "/Users/miitarou/Documents/New project/data/restaurants.json"
    
    with open(data_path, 'r', encoding='utf-8') as f:
        restaurants = json.load(f)
    
    print(f"=== 2017-2019 店舗IDマッチング v2 ===")
    print(f"全店舗: {len(restaurants)}")
    
    # 名前が数字のみ（= 前回のスクリプトで名前取得に失敗したもの）を除外して元に戻す
    original = [r for r in restaurants if not (r.get('name', '').isdigit() or len(r.get('name', '')) < 2)]
    removed = len(restaurants) - len(original)
    print(f"不正データ除外: {removed} 件")
    print(f"有効データ: {len(original)} 件")
    
    # 店舗IDでインデックスを構築
    id_index = {}
    for r in original:
        sid = extract_store_id(r['url'])
        if sid:
            id_index[sid] = r
    
    print(f"店舗IDインデックス: {len(id_index)} 件")
    
    # 前回取得した2017-2019のURL（fix_early_years.pyの結果から）を再利用
    # 前回のスクリプトで追加された不正エントリのURLから年度情報を復元
    early_year_entries = [r for r in restaurants if r.get('name', '').isdigit() or len(r.get('name', '')) < 2]
    
    # さらに、前回のスクリプトで正しくマッチしたものの年度情報も保持
    # ただし、既存店舗のyearsから2017/2018/2019が正しくマッチしたものもある
    
    # ここでは、不正エントリのURLと年度の情報を使って、IDマッチで再マッチング
    rematched = 0
    unmatched_ids = []
    
    for entry in early_year_entries:
        sid = extract_store_id(entry['url'])
        years_to_add = entry.get('years', [])
        
        if sid and sid in id_index:
            target = id_index[sid]
            if 'years' not in target or not isinstance(target['years'], list):
                target['years'] = []
            for y in years_to_add:
                if y not in target['years']:
                    target['years'].append(y)
            target['years'].sort()
            rematched += 1
        else:
            unmatched_ids.append((sid, entry['url'], years_to_add))
    
    print(f"\nIDマッチで復元: {rematched} 件")
    print(f"未マッチ: {len(unmatched_ids)} 件")
    
    if unmatched_ids:
        print("\n未マッチ店舗ID:")
        for sid, url, years in unmatched_ids[:20]:
            print(f"  ID:{sid} URL:{url} years:{years}")
    
    # 年度分布の確認
    year_counts = {}
    for r in original:
        for y in r.get('years', []):
            year_counts[y] = year_counts.get(y, 0) + 1
    print(f"\n年度分布: {dict(sorted(year_counts.items()))}")
    
    # 保存
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(original, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 保存完了: {len(original)} 店舗")


if __name__ == "__main__":
    main()
