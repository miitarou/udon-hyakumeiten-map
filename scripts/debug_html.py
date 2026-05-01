"""
食べログの店舗ページのHTML構造を調査するデバッグスクリプト
"""
import urllib.request

url = "https://tabelog.com/tokyo/A1302/A130204/13114085/"  # 谷や
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml',
    'Accept-Language': 'ja,en;q=0.5',
}
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req, timeout=15) as response:
    html = response.read().decode('utf-8', errors='replace')

# 住所周辺のHTMLを探す
import re

# "住所" というテキストの周辺を抽出
for keyword in ['address', '住所', 'streetAddress', 'rstinfo', 'locality']:
    idx = html.lower().find(keyword.lower())
    if idx >= 0:
        start = max(0, idx - 100)
        end = min(len(html), idx + 300)
        snippet = html[start:end]
        print(f"\n=== '{keyword}' found at {idx} ===")
        print(snippet)
        print("---")
