# アプリ構成メモ

現状のWeb版は、外部ビルドなしでGitHub Pagesに配信できる単一HTML/CSS/JS構成です。`app.js` は機能追加に伴って大きくなっているため、今後は段階的に責務を分けます。

## 現在の方針

- 公開直前やiPhone版申請直前は、大きな分割より小さな安全修正を優先する
- 分割する場合も、まずは素のES Modulesで始め、ビルド工程は増やさない
- Web版を正とし、iPhone版は同期スクリプトで同梱資産へ反映する

## 分割候補

| 候補ファイル | 責務 |
| --- | --- |
| `data-loader.js` | 店舗JSON、推薦タグ、データバージョンの読み込み |
| `map-view.js` | Leaflet、MarkerCluster、地図タイル、マーカー、ポップアップ |
| `filters.js` | 検索、カテゴリ、年度、選出回数、営業状態、距離、地図内フィルタ |
| `state-store.js` | localStorage、訪問状況、設定保存、設定復元 |
| `recommendation-engine.js` | 推薦スコア、理由生成、ゴールデンセットと同じロジック |
| `popup-view.js` | 店舗ポップアップ、推薦UI、外部リンク |
| `mobile-panel.js` | スマホ用ボトムシート、ドラッグ、閉じる挙動 |

## 推奨する移行順

1. 副作用が少ない推薦計算を `recommendation-engine.js` に切り出す
2. localStorage関連を `state-store.js` に切り出す
3. フィルタ状態とUI更新を `filters.js` に切り出す
4. Leaflet依存部分を最後に `map-view.js` へ分ける

地図とUIは相互依存が強いため、最初から全分割すると不具合が出やすくなります。まずは計算ロジックと保存ロジックから切り出すのが安全です。

## innerHTML利用ルール

`innerHTML` を使う場合は、以下を守ります。

- 店舗データ由来のテキストは必ず `escapeHtml()` を通す
- URLは `isSafeUrl()`、`encodeURIComponent()`、または信頼済みビルダーで作る
- 新規UIでは、可能な限り `document.createElement()` と `textContent` を使う
- 推薦タグは探索補助データであり、店舗評価や事実断定として表示しない

## CSP導入方針

GitHub PagesではHTTPヘッダーのCSPを細かく制御しにくいため、まずは `index.html` の `<meta http-equiv="Content-Security-Policy">` で弱めに導入します。

現在許可している主な外部先:

- Leaflet / MarkerCluster CDN: `https://unpkg.com`
- Google Fonts: `https://fonts.googleapis.com`, `https://fonts.gstatic.com`
- 地理院タイル: `https://cyberjapandata.gsi.go.jp`, `https://*.gsi.go.jp`
- OSM系画像: `https://*.openstreetmap.org`
- iPhone版データ更新: `https://miitarou.github.io`

今後CSPを強くする場合は、インラインstyle、地図タイル、Service Worker、外部フォント、Capacitor WebViewでの挙動をセットで検証します。
