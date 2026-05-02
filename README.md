# 🍜 うどん百名店 MAP 2017-2024

食べログ「うどん百名店」**2017〜2024年の全6回分、EAST × WEST 全364店舗**を地図上にプロットするインタラクティブWebアプリ。

🔗 **公開URL**: [https://miitarou.github.io/udon-hyakumeiten-map/](https://miitarou.github.io/udon-hyakumeiten-map/)

![Stores](https://img.shields.io/badge/全店舗-364-D4A853)
![EAST](https://img.shields.io/badge/EAST-202-2B4C7E)
![WEST](https://img.shields.io/badge/WEST-162-D4A853)
![License](https://img.shields.io/badge/license-MIT-blue)

## ✨ 特徴

### 🗺️ マップ機能
- **全364店舗マップ表示** — Leaflet.js + MarkerCluster による高速レンダリング
- **うどん丼SVGアイコン** — 選出回数に応じてサイズ・グロウ効果が変化する独自マーカー
- **店名ラベル自動表示** — マーカーが個別表示された瞬間に店名を自動表示（クリック不要）
- **現在地ボタン** — GPS連動で現在地周辺の名店を素早く探索

### 🔍 フィルタ・検索
- **EAST / WEST 切替** — 麦穂ゴールド × 藍色のテーマカラーで直感的に区別
- **店名・エリア検索** — リアルタイムインクリメンタル検索
- **都道府県フィルタ** — 全国から絞り込み
- **選出年フィルタ** — 2017 / 2018 / 2019 / 2020 / 2022 / 2024 の各年度で絞り込み
- **選出回数フィルタ** — 2回以上〜6回以上で常連名店を発見
- **特殊フィルタ** — 初選出のみ / 閉店を除外

### 🎨 デザイン
- **麦穂ゴールド × 藍色** — うどん（小麦）をテーマにした温かみのある配色
- **ダークモードUI** — グラスモーフィズムによるモダンなデザイン
- **レスポンシブ対応** — デスクトップ・モバイル両対応（下部ドロワーパネル）
- **選出回数による強調表示** — 1-2回：通常 / 3-4回：中サイズ / 5回以上：大サイズ＋ゴールドボーダー

### 📋 店舗リスト
- **ソート機能** — 名前順 / 選出回数順 / 都道府県順
- **カード表示** — 店名・エリア・選出回数・年度バッジを一覧表示
- **ワンタップで地図連動** — リストをタップするとマップ上の該当マーカーにフォーカス
- **食べログ直リンク** — ポップアップからワンクリックで食べログページへ

## 🚀 使い方

```bash
# ローカルサーバーで起動
python3 -m http.server 8080

# ブラウザで開く
open http://localhost:8080
```

## 📁 プロジェクト構造

```
├── index.html              # メインHTML
├── style.css               # スタイルシート (ダークモード + グラスモーフィズム)
├── app.js                  # アプリケーションロジック
├── data/
│   ├── restaurants.json        # 全364店舗データ (座標・選出年付き)
│   ├── restaurants_merged.json # 年度統合済みデータ
│   ├── all_years_raw.json      # 全年度の生データ
│   └── restaurants_raw.json    # 生データ (ジオコーディング前)
├── scripts/
│   ├── parse_restaurants.py        # HTMLから店舗データを解析
│   ├── collect_all_years.py        # 全年度のデータを収集・統合
│   ├── geocode_restaurants.py      # Nominatim ジオコーディング
│   ├── geocode_from_tabelog.py     # 食べログからの精密座標取得
│   ├── geocode_missing.py          # 座標未取得店舗の補完
│   ├── fetch_addresses.py          # 住所データ取得
│   ├── fix_early_years.py          # 初期年度データの修正
│   ├── check_years.py              # 年度データの検証
│   └── analyze_area_data.py        # エリアデータの分析
└── README.md
```

## 🛠️ 技術スタック

| カテゴリ | 技術 |
|---------|------|
| 地図描画 | [Leaflet.js](https://leafletjs.com/) v1.9.4 |
| クラスタリング | [Leaflet.markercluster](https://github.com/Leaflet/Leaflet.markercluster) |
| 地図タイル | [国土地理院タイル](https://maps.gsi.go.jp/) |
| フォント | [Noto Sans JP](https://fonts.google.com/noto/specimen/Noto+Sans+JP), [Outfit](https://fonts.google.com/specimen/Outfit) |
| データソース | [食べログ 百名店](https://award.tabelog.com/hyakumeiten/) |
| ジオコーディング | 食べログ店舗ページからの座標抽出 + Nominatim |
| ホスティング | [GitHub Pages](https://pages.github.com/) |

## 📊 データについて

- **対象**: 食べログ うどん百名店 2017〜2024（全6回分）
- **店舗数**: 全364店舗（EAST 202店 / WEST 162店）
- **選出年**: 2017, 2018, 2019, 2020, 2022, 2024
- **座標精度**: 食べログ店舗ページから直接取得（建物レベルの精度）
- **閉店情報**: 閉店店舗は取消線ラベル + グレー表示で区別

## 📝 ライセンス

MIT License

## 🙏 謝辞

- [食べログ](https://tabelog.com/) — 百名店データの提供元
- [国土地理院](https://www.gsi.go.jp/) — 地図タイル
- [OpenStreetMap](https://www.openstreetmap.org/) — 地図データ
- [Leaflet](https://leafletjs.com/) — 地図ライブラリ
