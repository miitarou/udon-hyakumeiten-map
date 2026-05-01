"""
食べログ うどん百名店の過去年度URL存在チェック
- 2017〜2024の各年度でEAST/WEST/統合版のどれが存在するか確認
"""
import urllib.request
import urllib.error

def check_url(url):
    """URLが200を返すかチェック"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'text/html',
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception as e:
        return str(e)

base = "https://award.tabelog.com/hyakumeiten"
variants = ["udon", "udon_east", "udon_west", "udon_tokyo"]
years = range(2017, 2026)

print("=== 食べログ うどん百名店 URL存在チェック ===\n")
print(f"{'年度':<6}", end="")
for v in variants:
    print(f"{v:<15}", end="")
print()
print("-" * 70)

import time

for year in years:
    print(f"{year:<6}", end="", flush=True)
    for v in variants:
        url = f"{base}/{v}/{year}"
        status = check_url(url)
        mark = "✅" if status == 200 else f"❌({status})"
        print(f"{mark:<15}", end="", flush=True)
        time.sleep(1)  # レート制限
    print()

print("\n完了")
