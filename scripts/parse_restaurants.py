"""
食べログ うどん百名店 2024 EAST/WEST データ解析スクリプト
スクレイピング済みのマークダウンファイルからレストランデータを抽出してJSONに変換する
"""
import re
import json
import os

def parse_restaurant_file(filepath, region):
    """マークダウンファイルからレストランデータを解析する"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    restaurants = []
    
    # 食べログのレストランURL パターン（都道府県/エリア/サブエリア/店舗ID）
    # マルチラインの markdown リンクを抽出
    pattern = r'\[([\s\S]*?)\]\((https://tabelog\.com/(\w+)/A\d+/A\d+/\d+/)\)'
    
    matches = re.finditer(pattern, content)
    
    for match in matches:
        link_text = match.group(1).strip()
        url = match.group(2)
        pref_code = match.group(3)  # URL内の都道府県コード (tokyo, saitama, etc.)
        
        # ナビゲーションリンクなどを除外
        # レストラン情報は通常、都道府県名を含む
        if len(link_text) < 5:
            continue
        
        # 初選出フラグの判定
        first_selected = False
        if '初選出' in link_text:
            first_selected = True
            link_text = link_text.replace('初選出', '').strip()
        
        # テキストを行に分割して空行を除去
        lines = [line.strip() for line in link_text.split('\n') if line.strip()]
        
        if len(lines) < 2:
            continue
        
        # 店名（最初の行）
        name = lines[0]
        
        # ナビゲーションリンクのテキストをスキップ
        skip_keywords = ['百名店', '境界線', '選出店一覧', 'レビュアー', 'TOP', 
                        '企業情報', '利用規約', '個人情報', '選出基準', 'ログイン',
                        'すべて', '北海道', '青森', '秋田', '山形', '岩手', '宮城',
                        '食堂', 'スペイン', 'ハンバーガー', 'とんかつ', 'ラーメン',
                        '焼き鳥', '鳥料理', '焼肉', '居酒屋', '立ち飲み', 'お好み焼き',
                        'ステーキ', 'そば', 'カフェ', '洋食', 'フレンチ', '創作料理',
                        'イタリアン', 'ピザ', '日本料理', '天ぷら', '寿司', 'すき焼き',
                        'カレー', 'アジア', 'うなぎ', '餃子', 'うどん 百', '和菓子',
                        'スイーツ', 'アイス', 'バー 百', 'パン 百', '喫茶店',
                        '新感覚', '細め', 'こんにちは']
        
        should_skip = False
        for kw in skip_keywords:
            if kw in name:
                should_skip = True
                break
        if should_skip:
            continue
        
        # 都道府県とエリアの取得（2行目）
        prefecture = ""
        area = ""
        holiday = ""
        
        # 都道府県名のリスト
        pref_names = [
            '北海道', '青森県', '岩手県', '宮城県', '秋田県', '山形県', '福島県',
            '茨城県', '栃木県', '群馬県', '埼玉県', '千葉県', '東京都', '神奈川県',
            '新潟県', '富山県', '石川県', '福井県', '山梨県', '長野県',
            '岐阜県', '静岡県', '愛知県', '三重県',
            '滋賀県', '京都府', '大阪府', '兵庫県', '奈良県', '和歌山県',
            '鳥取県', '島根県', '岡山県', '広島県', '山口県',
            '徳島県', '香川県', '愛媛県', '高知県',
            '福岡県', '佐賀県', '長崎県', '熊本県', '大分県', '宮崎県', '鹿児島県', '沖縄県'
        ]
        
        # 都道府県を含む行を探す
        pref_line_idx = -1
        for i, line in enumerate(lines):
            for pn in pref_names:
                if pn in line:
                    prefecture = pn
                    area = line.replace(pn, '').strip()
                    pref_line_idx = i
                    break
            if prefecture:
                break
        
        if not prefecture:
            continue
        
        # 定休日（都道府県の次の行以降）
        if pref_line_idx >= 0 and pref_line_idx + 1 < len(lines):
            holiday = lines[pref_line_idx + 1]
        
        # URL内の都道府県コードから都道府県を補完
        pref_code_map = {
            'hokkaido': '北海道', 'aomori': '青森県', 'iwate': '岩手県',
            'miyagi': '宮城県', 'akita': '秋田県', 'yamagata': '山形県',
            'fukushima': '福島県', 'ibaraki': '茨城県', 'tochigi': '栃木県',
            'gunma': '群馬県', 'saitama': '埼玉県', 'chiba': '千葉県',
            'tokyo': '東京都', 'kanagawa': '神奈川県', 'niigata': '新潟県',
            'toyama': '富山県', 'ishikawa': '石川県', 'fukui': '福井県',
            'yamanashi': '山梨県', 'nagano': '長野県', 'gifu': '岐阜県',
            'shizuoka': '静岡県', 'aichi': '愛知県', 'mie': '三重県',
            'shiga': '滋賀県', 'kyoto': '京都府', 'osaka': '大阪府',
            'hyogo': '兵庫県', 'nara': '奈良県', 'wakayama': '和歌山県',
            'tottori': '鳥取県', 'shimane': '島根県', 'okayama': '岡山県',
            'hiroshima': '広島県', 'yamaguchi': '山口県', 'tokushima': '徳島県',
            'kagawa': '香川県', 'ehime': '愛媛県', 'kochi': '高知県',
            'fukuoka': '福岡県', 'saga': '佐賀県', 'nagasaki': '長崎県',
            'kumamoto': '熊本県', 'oita': '大分県', 'miyazaki': '宮崎県',
            'kagoshima': '鹿児島県', 'okinawa': '沖縄県'
        }
        
        if not prefecture and pref_code in pref_code_map:
            prefecture = pref_code_map[pref_code]
        
        restaurant = {
            "name": name,
            "region": region,
            "prefecture": prefecture,
            "area": area,
            "holiday": holiday,
            "url": url,
            "lat": None,
            "lng": None,
            "closed": False,
            "firstSelected": first_selected
        }
        
        # 重複チェック（同じURLのものはスキップ）
        if not any(r['url'] == url for r in restaurants):
            restaurants.append(restaurant)
    
    return restaurants

def main():
    # スクレイピング済みファイルのパス
    east_file = "/Users/miitarou/.gemini/antigravity/brain/64e3df48-88fc-4e6c-9796-76e39627e1c8/.system_generated/steps/5/content.md"
    west_file = "/Users/miitarou/.gemini/antigravity/brain/64e3df48-88fc-4e6c-9796-76e39627e1c8/.system_generated/steps/21/content.md"
    
    print("=== EAST データ解析中... ===")
    east_restaurants = parse_restaurant_file(east_file, "EAST")
    print(f"EAST: {len(east_restaurants)} 店舗を検出")
    
    print("\n=== WEST データ解析中... ===")
    west_restaurants = parse_restaurant_file(west_file, "WEST")
    print(f"WEST: {len(west_restaurants)} 店舗を検出")
    
    # 統合
    all_restaurants = east_restaurants + west_restaurants
    print(f"\n=== 合計: {len(all_restaurants)} 店舗 ===")
    
    # 都道府県別の集計
    pref_count = {}
    for r in all_restaurants:
        pref = r['prefecture']
        pref_count[pref] = pref_count.get(pref, 0) + 1
    
    print("\n--- 都道府県別店舗数 ---")
    for pref, count in sorted(pref_count.items(), key=lambda x: -x[1]):
        print(f"  {pref}: {count}店")
    
    # 初選出の数
    first_selected_count = sum(1 for r in all_restaurants if r['firstSelected'])
    print(f"\n初選出: {first_selected_count} 店舗")
    
    # JSON出力
    output_dir = "/Users/miitarou/Documents/New project/data"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "restaurants_raw.json")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_restaurants, f, ensure_ascii=False, indent=2)
    
    print(f"\nJSON出力完了: {output_path}")
    
    # 最初の5件を表示して確認
    print("\n--- サンプルデータ（最初の5件）---")
    for r in all_restaurants[:5]:
        print(f"  {r['name']} ({r['region']}) - {r['prefecture']} {r['area']} - {r['url']}")

if __name__ == "__main__":
    main()
