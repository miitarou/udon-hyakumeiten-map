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
│   └── restaurants.json        # 全364店舗データ (座標・選出年付き)
├── scripts/
│   ├── parse_restaurants.py        # データ解析スクリプト
│   ├── collect_all_years.py        # 全年度のデータ収集・統合
│   ├── geocode_restaurants.py      # Nominatim ジオコーディング
│   ├── check_years.py              # 年度データの検証
│   └── analyze_area_data.py        # エリアデータの分析
├── DATA_LICENSE.md         # データ利用条件
└── README.md
```

## 🛠️ 技術スタック

| カテゴリ | 技術 |
|---------|------|
| 地図描画 | [Leaflet.js](https://leafletjs.com/) v1.9.4 |
| クラスタリング | [Leaflet.markercluster](https://github.com/Leaflet/Leaflet.markercluster) |
| 地図タイル | [地理院タイル（淡色地図）](https://maps.gsi.go.jp/development/ichiran.html)　出典：国土地理院 |
| フォント | [Noto Sans JP](https://fonts.google.com/noto/specimen/Noto+Sans+JP), [Outfit](https://fonts.google.com/specimen/Outfit) |
| ホスティング | [GitHub Pages](https://pages.github.com/) |

## 📊 データについて

本サイトは、公開情報をもとに個人が整理した**非公式の参考マップ**です。

- **対象**: うどん百名店 2017〜2024（全6回分）の店舗情報
- **店舗数**: 全364店舗（EAST 202店 / WEST 162店）
- **選出年**: 2017, 2018, 2019, 2020, 2022, 2024
- **閉店情報**: 閉店店舗は取消線ラベル + グレー表示で区別

⚠️ 掲載情報の正確性、完全性、最新性は保証しません。
営業時間、定休日、閉店・移転状況、予約可否等は、来店前に必ず公式情報または[食べログ](https://tabelog.com/)店舗ページでご確認ください。

## ⚖️ ライセンス

**ソースコードは MIT License で提供します。**

ただし、`data/` 配下の店舗データ（店舗名、選出年度、住所、座標、URL、閉店情報等）は **MIT License の対象外** です。
詳細は [DATA_LICENSE.md](DATA_LICENSE.md) をご確認ください。

## ⚠️ 免責事項

本サイトは個人が作成した**非公式のファンツール**です。
食べログ、株式会社カカクコム、食べログ 百名店とは**提携・協賛・承認関係にありません**。

現在地情報はブラウザ上でのみ使用し、サーバーへの送信・保存は一切行いません。

## 🙏 謝辞

- [食べログ](https://tabelog.com/) — 百名店情報の参照元
- [国土地理院](https://www.gsi.go.jp/) — [地理院タイル](https://maps.gsi.go.jp/development/ichiran.html)
- [OpenStreetMap](https://www.openstreetmap.org/) — 地図データ / [Nominatim](https://nominatim.org/)（ジオコーディング）
- [Leaflet](https://leafletjs.com/) — 地図ライブラリ
