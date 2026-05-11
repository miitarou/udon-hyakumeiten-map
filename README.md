# 🍜🥢 うどん・そば百名店 MAP 2017-2025

公開されている「うどん・そば百名店」関連情報をもとに、個人が整理した非公式の参考マップです。
うどん・そばの店舗を地図上で確認でき、ジャンル切替、年度フィルタ、地域フィルタ、選出回数フィルタに対応しています。
本サイトは、食べログ、株式会社カカクコム、食べログ百名店とは提携・協賛・承認関係にありません。

🔗 **公開URL**: [https://miitarou.github.io/udon-hyakumeiten-map/](https://miitarou.github.io/udon-hyakumeiten-map/)

![Udon](https://img.shields.io/badge/うどん-428店-D4A853)
![Soba](https://img.shields.io/badge/そば-266店-7B9E6B)
![Total](https://img.shields.io/badge/合計-694店-555555)
![License](https://img.shields.io/badge/license-MIT-blue)

## ✨ 特徴

### 🗂️ ジャンル切替
- **ALL / 🍜 うどん / 🥢 そば** — ヘッダーのトグルでワンタップ切替、同時表示も可能
- **カテゴリ別マーカー** — うどん（青・ゴールド・テラコッタ）/ そば（ティール・グリーン）で識別
- **カテゴリ別アイコン** — うどん：丼鉢SVG / そば：猪口SVGを独自デザイン

### 🗺️ マップ機能
- **694店舗マップ表示** — Leaflet.js + MarkerCluster による高速レンダリング
- **選出回数による強調** — 中サイズ / カテゴリ別の選出回数上位10%相当（殿堂入り）クラス：大サイズ＋殿堂ボーダー
- **店名ラベル自動表示** — マーカー個別表示時に自動表示（クリック不要）
- **現在地ボタン** — GPS連動で現在地周辺の名店を素早く探索

### 🔍 フィルタ・検索
- **EAST / WEST / KAGAWA 切替** — うどんのみKAGAWA対応（2024年独立カテゴリ）
- **店名・住所・駅名検索** — リアルタイム検索。かな・カナ、旧字体の一部、軽微な打ち間違いを吸収
- **都道府県フィルタ** — 全国から絞り込み
- **選出年フィルタ** — カテゴリに応じて利用可能年度を動的生成
  - うどん：2017 / 2018 / 2019 / 2020 / 2022 / 2024
  - そば：2017 / 2018 / 2019 / 2021 / 2022 / 2024 / 2025
- **選出回数フィルタ** — 最新年度で初登場 / 1回のみ / 2回以上〜4回以上 / 殿堂入り（カテゴリ上位10%）で絞り込み
- **距離検索** — 現在地または地図クリック地点から半径検索
- **訪問状況** — 行きたい / 訪問済みをブラウザに保存し、JSONによる設定保存・設定復元に対応
- **この店が好きなら** — 店舗ポップアップから、静的なAI推定タグに基づく類似・近接候補を表示

保存情報はブラウザの `localStorage` にのみ保存され、サーバーには送信されません。
ブラウザ変更、端末変更、サイトデータ削除により失われる可能性があるため、必要に応じて設定保存をご利用ください。

### 🎨 デザイン
- **ダークモードUI** — グラスモーフィズムによるモダンなデザイン
- **レスポンシブ対応** — デスクトップ（サイドパネル）・モバイル（下部ドロワー）両対応
- **パネル幅リサイズ** — PC版はドラッグで自由に幅調整（280〜600px）
- **PWA対応** — manifest と Service Worker により、再訪時の基本アセットと店舗JSONをキャッシュ。更新通知とオフライン時の案内にも対応

### 📋 店舗リスト
- **ソート機能** — 名前順 / 選出回数順 / 都道府県順 / 現在地から近い順
- **カード表示** — 店名・エリア・選出回数・年度バッジを一覧表示
- **ワンタップで地図連動** — リストをタップするとマップ上の該当マーカーにフォーカス
- **食べログ直リンク + Googleで見る** — ポップアップから各店舗情報へワンクリックで遷移

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
├── manifest.webmanifest        # PWAマニフェスト
├── sw.js                       # Service Worker
├── icon.svg                    # PWAアイコン
├── privacy.html                # プライバシーポリシー
├── docs/
│   └── recommendation-tags.md  # 推薦タグとスコアリング設計
├── data/
│   ├── data-version.json       # iPhone版向けデータ更新メタ情報
│   ├── recommendation_tags.json # 推薦機能向けの静的タグデータ（探索補助用）
│   ├── recommendation_golden_set.json # 推薦品質確認用の代表ケース
│   ├── udon.json               # うどん百名店データ（428店）
│   ├── udon_raw.json           # うどんデータ生成元（ジオコーディング前）
│   ├── soba.json               # そば百名店データ（266店）
│   └── soba_raw.json           # そばデータ生成元（ジオコーディング前）
├── scripts/
│   ├── build_udon_json.py      # うどんデータ年度別マージ・生成スクリプト
│   ├── geocode_udon.py         # うどん店舗 Nominatim ジオコーディング
│   ├── build_soba_json.py      # そばデータ年度別マージ・生成スクリプト
│   ├── geocode_soba.py         # そば店舗 Nominatim ジオコーディング
│   ├── fetch_tabelog_details.py # 店舗ページ由来の住所・座標・閉店状態取得
│   ├── generate_recommendation_tags.py # 推薦タグデータ生成
│   ├── evaluate_recommendations.py # 推薦ゴールデンセットの結果レポート
│   ├── generate_data_version.py # iPhone版向けデータメタ情報生成
│   ├── sync_mobile_assets.py   # Web資産を mobile/www へ同期
│   └── check_data_quality.py   # 公開データ品質チェック
├── mobile/                     # Capacitor iOSラッパー
│   ├── capacitor.config.json   # iOSアプリ設定
│   ├── package.json            # Capacitor依存とモバイル用npm scripts
│   ├── vendor/                 # iOS同梱用の固定化済み地図ライブラリ
│   └── www/                    # Web資産同期先
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

Leaflet / Leaflet.markercluster の CDN 読み込みには Subresource Integrity (SRI) を設定しています。

## 📊 データについて

本サイトは、公開されている『うどん・そば百名店』関連情報をもとに、個人が独自に整理・構築した**非公式の参考マップ**です。
座標は住所・店舗ページ等から推定しており、誤差が生じる場合があります。

「殿堂入り」は公式称号ではなく、本サイト内での表示上の便宜的な分類です。
固定の選出回数ではなく、うどん・そばそれぞれのカテゴリ別全体データにおける選出回数上位10%相当を基準にしています。

### 推薦タグデータ

`data/recommendation_tags.json` は、店舗ポップアップの「この店が好きなら」表示に使う静的タグデータです。
既存データから確定できるジャンル・地域・選出履歴タグと、店名・地域・選出履歴から控えめに推定した探索補助タグを分けて保持しています。
推定タグは店舗説明の事実断定ではなく、店舗間の類似度計算に使うための補助情報です。

タグ辞書、`weight` / `confidence`、類似度計算、推薦モードの設計方針は [docs/recommendation-tags.md](docs/recommendation-tags.md) にまとめています。

### うどん百名店
- **対象**: 2017〜2024年（全6回分）
- **店舗数**: 428店（EAST 212店 / WEST 111店 / KAGAWA 105店）
- **年度・カテゴリ構成**:
  - 2017/2018/2019：全国100店（単一リスト）
  - 2020：TOKYO 100店 + EAST 100店 + WEST 100店（TOKYO はEASTとして統合）
  - 2022：EAST 100店 + WEST 100店
  - 2024：EAST 100店 + WEST 100店 + **KAGAWA 100店**（香川県が独立カテゴリとして初登場）

### そば百名店
- **対象**: 2017〜2025年（全7回分）
- **店舗数**: 266店（EAST 157店 / WEST 109店）
- **選出年**: 2017, 2018, 2019, 2021, 2022, 2024, 2025
- **注記**: 2024年以降 EAST/WEST 分割。2020・2023年は非開催。

⚠️ **重要:** 掲載情報の正確性、完全性、および最新状況は一切保証いたしません。
店舗の移転、閉店、営業時間変更等の可能性があります。
参考情報としてのみ利用し、実際に訪問される際は、必ず公式サイトや[食べログ](https://tabelog.com/)等で最新の公式情報をご確認ください。

## 🧪 データ更新・検証

本リポジトリではデータ品質を保つために検証スクリプトを提供しています。データを更新した際は、以下の手順で検証を行ってください。

1. `data/udon.json` または `data/soba.json` を更新する
2. iPhone版向けのデータメタ情報と推薦タグを更新する
   ```bash
   python3 scripts/generate_data_version.py
   python3 scripts/generate_recommendation_tags.py
   ```
3. 以下のコマンドで検証スクリプトを実行する
   ```bash
   python3 scripts/check_data_quality.py
   ```
4. エラーが出た場合はデータを修正し、ローカルサーバーで動作確認を行う

主な検証内容:

- JSON構文とルート配列
- 必須項目（店舗名、都道府県、地域、緯度、経度、選出年）
- カテゴリ値と地域値
- 緯度・経度の範囲
- 年度値
- URL形式と許可ホスト
- HTMLタグ混入
- `closed` / `firstSelected` のboolean形式
- 店名 + 都道府県による重複候補
- `data/data-version.json` の件数・ハッシュ整合
- `data/recommendation_tags.json` のURL照合・タグ定義・weight/confidence形式・AI推定相性グループ
- `data/recommendation_golden_set.json` の参照URL・推薦モード整合

推薦品質を確認する場合は、代表ケース（36ケース）に対する現行推薦結果を出力します。

```bash
python3 scripts/evaluate_recommendations.py
```

特定ケースだけ確認する場合:

```bash
python3 scripts/evaluate_recommendations.py --case udon_tokyo_maruka_similar --top 9
```

## 📱 iPhone版

同一リポジトリ内の `mobile/` にCapacitorベースのiOSラッパーを置いています。
Web版の `index.html` / `style.css` / `app.js` / `data/*.json` を正とし、以下でiPhone版の同梱資産へ同期します。

```bash
cd mobile
npm run ios:sync
```

iPhone版では、HTML/CSS/JSはアプリに同梱し、機能変更はApp Storeアップデートで反映します。
店舗JSONのみ起動時にGitHub Pages上の最新版取得を試み、失敗時は端末キャッシュ、さらに失敗時はアプリ同梱JSONへフォールバックします。

- Bundle ID: `jp.miitarou.hyakumeiten.udonsoba`
- 表示名: `うどん・そば百名店MAP`
- 位置情報は現在地周辺の店舗検索にのみ使用し、サーバー送信・保存は行いません。

## ⚖️ ライセンス

**ソースコードは MIT License で提供します。** 詳細は [LICENSE](LICENSE) をご確認ください。

`data/` 配下の店舗データ（店舗名、選出年度、住所、座標、URL等）は **MIT License の対象外** です。
詳細は [DATA_LICENSE.md](DATA_LICENSE.md) をご確認ください。

## ⚠️ 免責事項

本サイトは個人が作成した**非公式のファンツール**です。
食べログ、株式会社カカクコム、食べログ百名店とは**提携・協賛・承認関係にありません**。

現在地情報はブラウザ上でのみ使用し、サーバーへの送信・保存は一切行いません。

## 🙏 謝辞

- [食べログ](https://tabelog.com/) — 百名店情報の参照元
- [国土地理院](https://www.gsi.go.jp/) — [地理院タイル](https://maps.gsi.go.jp/development/ichiran.html)
- [OpenStreetMap](https://www.openstreetmap.org/) — 地図データ / [Nominatim](https://nominatim.org/)（ジオコーディング）
- [Leaflet](https://leafletjs.com/) — 地図ライブラリ
