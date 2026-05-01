"""
2017-2019のページが取得できるか確認するスクリプト
"""
import urllib.request
import urllib.error
import re
import time

URLS = [
    ("2017 ALL", "https://award.tabelog.com/hyakumeiten/udon/2017"),
    ("2018 ALL", "https://award.tabelog.com/hyakumeiten/udon/2018"),
    ("2019 ALL", "https://award.tabelog.com/hyakumeiten/udon/2019"),
    ("2020 EAST", "https://award.tabelog.com/hyakumeiten/udon_east/2020"),
    ("2020 WEST", "https://award.tabelog.com/hyakumeiten/udon_west/2020"),
    ("2020 TOKYO", "https://award.tabelog.com/hyakumeiten/udon_tokyo/2020"),
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'text/html',
    'Accept-Language': 'ja,en;q=0.5',
}

for label, url in URLS:
    print(f"\n=== {label}: {url} ===")
    time.sleep(2)
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode('utf-8', errors='replace')
            status = resp.status
            print(f"  ステータス: {status}")
            print(f"  HTMLサイズ: {len(html)} bytes")
            
            # hyakumeiten-shop__target の数
            targets = re.findall(r'hyakumeiten-shop__target', html)
            print(f"  hyakumeiten-shop__target: {len(targets)} 個")
            
            # img alt抽出テスト
            pattern = re.compile(
                r'hyakumeiten-shop__target[^"]*"[^>]*href="(https://tabelog\.com/[^"]+)"'
                r'[^>]*>.*?<img\s+alt="([^"]*)"',
                re.DOTALL
            )
            matches = pattern.findall(html)
            print(f"  店舗抽出数: {len(matches)}")
            if matches:
                for m in matches[:3]:
                    print(f"    - {m[1]} ({m[0][:50]}...)")
            else:
                # 別のパターンを試す
                alt_pattern = re.findall(r'<img\s+alt="([^"]+)"', html)
                print(f"  img alt全体: {len(alt_pattern)} 個")
                if alt_pattern:
                    for a in alt_pattern[:5]:
                        print(f"    - alt: {a}")
                
                # ページ内のリンクパターン
                links = re.findall(r'href="(https://tabelog\.com/[^"]*)"', html)
                print(f"  tabelog リンク: {len(links)} 個")
                if links:
                    for l in links[:3]:
                        print(f"    - {l}")
                        
    except urllib.error.HTTPError as e:
        print(f"  ❌ HTTP {e.code}")
    except Exception as e:
        print(f"  ❌ {e}")
