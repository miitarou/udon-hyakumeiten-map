# アプリ構成メモ

現状のWeb版は、外部ビルドなしでGitHub Pagesに配信できるHTML/CSS/JS構成です。`app.js` は機能追加に伴って大きくなっているため、今後も段階的に責務を分けます。

第一段階として、推薦スコア計算・理由生成・表示スコア正規化は `recommendation-engine.js` に切り出し済みです。`app.js` は classic script のまま維持し、推薦タグ利用時に `import('./recommendation-engine.js?...')` で動的に読み込みます。これにより、推薦エンジンの読み込みに失敗しても、地図・検索・フィルタ本体は動き続けます。

次の小分割として、検索正規化・かな揺らぎ・あいまい検索だけを `search.js` に切り出しています。`search.js` は classic script として `app.js` より先に読み込み、`window.HyakumeitenSearch` に純粋関数を公開します。

## 現在の方針

- 公開直前やiPhone版申請直前は、大きな分割より小さな安全修正を優先する
- 分割する場合も、まずは素のES Modulesで始め、ビルド工程は増やさない
- 純粋計算ロジックはES Moduleへ寄せ、DOM・Leaflet・localStorage依存は `app.js` 側に残す
- Web版を正とし、iPhone版は同期スクリプトで同梱資産へ反映する

## 現在の分担

| 候補ファイル | 責務 |
| --- | --- |
| `app.js` | 地図、フィルタUI、ポップアップ、推薦UI、訪問状況、モバイルUI |
| `search.js` | 検索語の正規化、店名・住所・駅名検索、軽いあいまい検索 |
| `recommendation-engine.js` | 推薦タグのインデックス化、スコア計算、理由生成、表示スコア正規化 |

`recommendation-engine.js` は、DOM、Leaflet、localStorage、`escapeHtml()` に依存しない純粋ロジックとして扱います。UI表示、HTML生成、クリックイベント、ポップアップ位置調整は引き続き `app.js` の責務です。

## 次の分割候補

| 候補ファイル | 責務 |
| --- | --- |
| `data-loader.js` | 店舗JSON、推薦タグ、データバージョンの読み込み |
| `map-view.js` | Leaflet、MarkerCluster、地図タイル、マーカー、ポップアップ |
| `filters.js` | カテゴリ、年度、選出回数、営業状態、距離、地図内フィルタ |
| `state-store.js` | localStorage、訪問状況、設定保存、設定復元 |
| `popup-view.js` | 店舗ポップアップ、推薦UI、外部リンク |
| `mobile-panel.js` | スマホ用ボトムシート、ドラッグ、閉じる挙動 |

## 推奨する移行順

1. 推薦計算を `recommendation-engine.js` に切り出す（完了）
2. 検索ユーティリティを `search.js` に切り出す（完了）
3. localStorage関連を `state-store.js` に切り出す
4. フィルタ状態とUI更新を `filters.js` に切り出す
5. Leaflet依存部分を最後に `map-view.js` へ分ける

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
- OpenFreeMap試験レイヤ: `https://tiles.openfreemap.org`
- MapLibre動的ロードとworker: `https://unpkg.com`, `blob:`
- iPhone版データ更新: `https://miitarou.github.io`

今後CSPを強くする場合は、インラインstyle、地図タイル、Service Worker、外部フォント、Capacitor WebViewでの挙動をセットで検証します。
