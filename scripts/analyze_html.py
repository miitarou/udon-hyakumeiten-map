"""
食べログ百名店ページのHTML構造を調査するスクリプト
- サンプルページをダウンロードして店舗リンクパターンを分析
"""
import urllib.request
import re
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html',
    'Accept-Language': 'ja,en;q=0.5',
}

# 2022年EASTページを取得して構造を分析
url = "https://award.tabelog.com/hyakumeiten/udon_east/2022"
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req, timeout=15) as resp:
    html = resp.read().decode('utf-8', errors='replace')

# HTMLをファイルに保存
with open("/Users/miitarou/Documents/New project/data/sample_2022.html", 'w', encoding='utf-8') as f:
    f.write(html)

print(f"HTML長: {len(html)} bytes")

# 食べログ店舗URLパターンを検索
url_pattern = re.compile(r'https?://tabelog\.com/([a-z_]+)/A(\d{4})/A\d+/(\d+)/?')
urls = list(set(m.group(0) for m in url_pattern.finditer(html)))
print(f"\n食べログ店舗URL数: {len(urls)}")
for u in sorted(urls)[:5]:
    print(f"  {u}")

# 各URLの前後100文字を表示して構造を把握
print("\n=== URL周辺のHTMLコンテキスト ===")
for u in sorted(urls)[:3]:
    idx = html.find(u)
    if idx >= 0:
        start = max(0, idx - 200)
        end = min(len(html), idx + len(u) + 200)
        snippet = html[start:end]
        # タグを見やすく改行
        snippet = re.sub(r'><', '>\n<', snippet)
        print(f"\n--- {u} ---")
        print(snippet)
        print()
