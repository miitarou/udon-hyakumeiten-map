# 🍜🥢 うどん・そば百名店 MAP 2017-2025

食べログ「**うどん百名店**」2017〜2024年・「**そば百名店**」2017〜2025年の全店舗を地図上にプロットするインタラクティブWebアプリ。うどん・そば切替、または同時表示に対応。

🔗 **公開URL**: [https://miitarou.github.io/udon-hyakumeiten-map/](https://miitarou.github.io/udon-hyakumeiten-map/)

![Udon](https://img.shields.io/badge/うどん-432店-D4A853)
![Soba](https://img.shields.io/badge/そば-267店-7B9E6B)
![Total](https://img.shields.io/badge/合計-699店-555555)
![License](https://img.shields.io/badge/license-MIT-blue)

## ✨ 特徴

### 🗂️ ジャンル切替
- **ALL / 🍜 うどん / 🥢 そば** — ヘッダーのトグルでワンタップ切替、同時表示も可能
- **カテゴリ別マーカー** — うどん（青・ゴールド・テラコッタ）/ そば（ティール・グリーン）で識別
- **カテゴリ別アイコン** — うどん：丼鉢SVG / そば：猪口SVGを独自デザイン

### 🗺️ マップ機能
- **699店舗マップ表示** — Leaflet.js + MarkerCluster による高速レンダリング
- **選出回数による強調** — 3-4回：中サイズ / 5回以上：大サイズ＋殿堂ボーダー
- **店名ラベル自動表示** — マーカー個別表示時に自動表示（クリック不要）
- **現在地ボタン** — GPS連動で現在地周辺の名店を素早く探索

### 🔍 フィルタ・検索
- **EAST / WEST / KAGAWA 切替** — うどんのみKAGAWA対応（2024年独立カテゴリ）
- **店名・エリア検索** — リアルタイムインクリメンタル検索
- **都道府県フィルタ** — 全国から絞り込み
- **選出年フィルタ** — カテゴリに応じて利用可能年度を動的生成
  - うどん：2017 / 2018 / 2019 / 2020 / 2022 / 2024
  - そば：2017 / 2018 / 2019 / 2021 / 2022 / 2024 / 2025
- **選出回数フィルタ** — 2回以上〜6回以上で常連名店を発見
- **初選出フィルタ** — 新顔店舗だけを表示
- **👑 殿堂入りモード** — 5回以上選出の名店だけを表示

### 🎨 デザイン
- **ダークモードUI** — グラスモーフィズムによるモダンなデザイン
- **レスポンシブ対応** — デスクトップ（サイドパネル）・モバイル（下部ドロワー）両対応
- **パネル幅リサイズ** — PC版はドラッグで自由に幅調整（280〜600px）

### 📋 店舗リスト
- **ソート機能** — 名前順 / 選出回数順 / 都道府県順 / 現在地から近い順
- **カード表示** — 店名・エリア・選出回数・年度バッジを一覧表示
- **ワンタップで地図連動** — リストをタップするとマップ上の該当マーカーにフォーカス
- **食べログ直リンク + Google Maps 経路** — ポップアップからワンクリックで遷移

## 🚀 使い方

```bash
# ローカルサーバーで起動
python3 -m http.server 8080

# ブラウザで開く
open http://localhost:8080
```

## 📁 プロジェクト構造

```
├── index.html                  # メインHTML
├── style.css                   # スタイルシート (ダークモード + グラスモーフィズム)
├── app.js                      # アプリケーションロジック
├── data/
│   ├── udon.json               # うどん百名店データ（432店）
│   ├── udon_raw.json           # うどんデータ生成元（ジオコーディング前）
│   ├── soba.json               # そば百名店データ（267店）
│   └── soba_raw.json           # そばデータ生成元（ジオコーディング前）
├── scripts/
│   ├── build_udon_json.py      # うどんデータ年度別マージ・生成スクリプト
│   ├── geocode_udon.py         # うどん店舗 Nominatim ジオコーディング
│   ├── build_soba_json.py      # そばデータ年度別マージ・生成スクリプト
│   └── geocode_soba.py         # そば店舗 Nominatim ジオコーディング
├── LICENSE                     # MIT License
├── DATA_LICENSE.md             # データ利用条件
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
座標は住所・店舗ページ等から推定しており、誤差が生じる場合があります。

### うどん百名店
- **対象**: 2017〜2024年（全6回分）
- **店舗数**: 432店（EAST 212店 / WEST 113店 / KAGAWA 107店）
- **年度・カテゴリ構成**:
  - 2017/2018/2019：全国100店（単一リスト）
  - 2020：TOKYO 100店 + EAST 100店 + WEST 100店（TOKYO はEASTとして統合）
  - 2022：EAST 100店 + WEST 100店
  - 2024：EAST 100店 + WEST 100店 + **KAGAWA 100店**（香川県が独立カテゴリとして初登場）

### そば百名店
- **対象**: 2017〜2025年（全7回分）
- **店舗数**: 267店（EAST 158店 / WEST 109店）
- **選出年**: 2017, 2018, 2019, 2021, 2022, 2024, 2025
- **注記**: 2024年以降 EAST/WEST 分割。2020・2023年は非開催。

⚠️ 掲載情報の正確性、完全性、最新性は保証しません。
来店前に必ず公式情報または[食べログ](https://tabelog.com/)店舗ページでご確認ください。

## ⚖️ ライセンス

**ソースコードは MIT License で提供します。** 詳細は [LICENSE](LICENSE) をご確認ください。

`data/` 配下の店舗データ（店舗名、選出年度、住所、座標、URL等）は **MIT License の対象外** です。
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
