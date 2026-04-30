# 🍜 うどん百名店 MAP 2024

食べログ「うどん百名店 2024」 **EAST × WEST 全200店舗** を地図上にプロットするインタラクティブWebアプリ。

![Status](https://img.shields.io/badge/stores-196-orange)
![License](https://img.shields.io/badge/license-MIT-blue)

## ✨ 特徴

- 🗺️ **全店舗マップ表示** — Leaflet.js + MarkerCluster による高速レンダリング
- 🎨 **EAST / WEST 色分け** — ティール(EAST) × ピンク(WEST) の直感的なカラーリング
- 🔍 **店名・エリア検索** — リアルタイムインクリメンタル検索
- 🗾 **都道府県フィルタ** — 18都道府県から絞り込み
- ⭐ **初選出フィルタ** — 2024年に新たに選ばれた店舗をハイライト
- 🔗 **食べログ直リンク** — ポップアップからワンクリックで食べログページへ
- 📱 **レスポンシブ対応** — デスクトップ・モバイル両対応
- 🌙 **ダークモードUI** — グラスモーフィズムによるモダンなデザイン

## 🚀 使い方

```bash
# ローカルサーバーで起動
python3 -m http.server 8080

# ブラウザで開く
open http://localhost:8080
```

## 📁 プロジェクト構造

```
├── index.html          # メインHTML
├── style.css           # スタイルシート (ダークモード + グラスモーフィズム)
├── app.js              # アプリケーションロジック
├── data/
│   ├── restaurants.json     # 全店舗データ (座標付き)
│   └── restaurants_raw.json # 生データ (ジオコーディング前)
├── scripts/
│   ├── parse_restaurants.py       # データ解析スクリプト
│   ├── geocode_restaurants.py     # Nominatim ジオコーディング
│   └── geocode_from_tabelog.py    # 食べログからの精密座標取得
└── README.md
```

## 🛠️ 技術スタック

| カテゴリ | 技術 |
|---------|------|
| 地図描画 | [Leaflet.js](https://leafletjs.com/) v1.9.4 |
| クラスタリング | [Leaflet.markercluster](https://github.com/Leaflet/Leaflet.markercluster) |
| 地図タイル | [CartoDB Voyager](https://carto.com/basemaps/) |
| フォント | [Noto Sans JP](https://fonts.google.com/noto/specimen/Noto+Sans+JP), [Outfit](https://fonts.google.com/specimen/Outfit) |
| データソース | [食べログ 百名店](https://award.tabelog.com/hyakumeiten/) |
| ジオコーディング | 食べログ店舗ページからの座標抽出 |

## 📊 データについて

- **対象**: 食べログ うどん百名店 2024 (EAST 100店 + WEST 100店)
- **座標精度**: 食べログ店舗ページから直接取得（建物レベルの精度）
- **更新日**: 2024年選出データ

## 📝 ライセンス

MIT License

## 🙏 謝辞

- [食べログ](https://tabelog.com/) — 百名店データの提供元
- [OpenStreetMap](https://www.openstreetmap.org/) — 地図データ
- [CARTO](https://carto.com/) — 地図タイル
