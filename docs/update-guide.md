# データ更新・検証ガイド

このリポジトリでは、Web版を正とし、iPhone版はWeb資産を同期して利用します。店舗データや推薦タグを更新した場合は、この順番で確認します。

## 1. 店舗データを更新する

対象は主に以下です。

- `data/udon.json`
- `data/soba.json`
- `data/udon_raw.json`
- `data/soba_raw.json`

店舗名、住所、座標、URL、閉店・移転情報、選出年度を更新した場合は、来店前確認を促す免責文と矛盾しないように扱います。

## 2. メタ情報と推薦タグを再生成する

```bash
python3 scripts/generate_data_version.py
python3 scripts/generate_external_signals.py
python3 scripts/generate_recommendation_tags.py
```

`data/data-version.json` は、iPhone版が起動時に最新版JSONを確認するためのメタ情報です。店舗JSONの件数やハッシュが変わった場合は必ず更新します。

`data/external_source_registry.json` を変更した場合も、`generate_external_signals.py` を実行してから推薦タグを再生成します。外部シグナルは短い根拠語だけを保持し、口コミ本文・点数・写真・SNS投稿は保存しません。詳しくは [external-signals.md](external-signals.md) を参照してください。

## 3. 推薦品質を確認する

推薦タグを変更した場合は、ゴールデンセットの結果も確認します。

```bash
python3 scripts/evaluate_recommendations.py
python3 scripts/evaluate_recommendations.py --case udon_tokyo_maruka_similar --top 9
```

このレポートは正解判定ではなく、代表ケースで推薦結果が大きく退行していないかを見るためのものです。

## 4. データ品質チェックを実行する

```bash
python3 scripts/check_data_quality.py
node --check app.js
node --check sw.js
git diff --check
```

主な検証対象は以下です。

- JSON構文とルート配列
- 必須項目
- 緯度・経度の範囲
- 年度値
- URL形式と許可ホスト
- HTMLタグ混入
- 重複候補
- `closed` / `firstSelected` の型
- 外部シグナル、推薦タグ、ゴールデンセットの参照整合

## 5. Web版をローカル確認する

```bash
python3 -m http.server 8080
open http://localhost:8080
```

最低限、以下を確認します。

- 初期表示で店舗が表示される
- 検索、フィルタ、地図内リストが動く
- 「この店が好きなら」の推薦候補が表示される
- 訪問状況、設定保存、設定復元が動く
- ブラウザコンソールにCSP違反やJavaScriptエラーが出ていない

## 6. iPhone版へ同期する

Web版の変更をiPhone同梱資産へ反映する場合は、以下を実行します。

```bash
cd mobile
npm run ios:sync
```

iPhone版では、HTML/CSS/JSはアプリ同梱です。UIや機能変更はApp Storeアップデートで反映します。店舗JSONのみ、起動時にGitHub Pages上の最新版取得を試みます。

## 7. Service Workerとキャッシュを確認する

`app.js`、`style.css`、`index.html`、主要データの読み込みに影響する変更を行った場合は、`sw.js` の `CACHE_NAME` とキャッシュ対象のクエリバージョンも更新します。

例:

```js
const CACHE_NAME = 'hyakumeiten-map-v26';
```

古いService Workerが残ると、ユーザーに旧JS/CSSが表示されることがあります。更新通知とリロード導線が動くことも確認します。

## 8. 公開前チェック

```bash
git status --short
git log --oneline -3
```

GitHub Actions の `Data Quality Check` が成功していることを確認します。iPhone版を申請する場合は、`mobile/APP_STORE_SUBMISSION_CHECKLIST.md` も合わせて確認します。
