# External Signals PoC

`external_signals` は、「この店が好きなら」推薦を少しだけ実店舗文脈に寄せるための補助データです。
実行時にLLM/APIを呼ばず、GitHub Actions上でも再現できる定型処理だけで生成します。

## 方針

- 外部ページ本文、口コミ本文、点数、写真、SNS投稿、ユーザー名は保存しません。
- 保存するのは、人間が確認した短い根拠語だけです。
- 根拠語は `scripts/generate_external_signals.py` の固定辞書で既存タグに変換します。
- 生成された `data/external_signals.json` を `data/recommendation_tags.json` に取り込みます。
- 推薦UIでは、店舗評価ではなく探索補助として扱います。

## 初期PoC

初期PoCでは、殿堂入り相当店舗から固定seedで20店舗を抽出しました。

- seed: `20260512`
- うどん殿堂入りしきい値: 6回以上
- そば殿堂入りしきい値: 4回以上
- 対象件数: 20件

外部情報は `data/external_source_registry.json` に登録します。
このファイルは収集済みの事実データではなく、短い根拠語のレビュー台帳です。

## 生成フロー

```bash
python3 scripts/generate_external_signals.py
python3 scripts/generate_recommendation_tags.py
python3 scripts/check_data_quality.py
python3 scripts/evaluate_recommendations.py > build/recommendation-report.md
```

`--check` を付けると、生成済みファイルが古くないかだけを確認できます。

```bash
python3 scripts/generate_external_signals.py --check
```

## sourceType

| sourceType | 用途 |
| --- | --- |
| `official_site` | 店舗公式サイト |
| `official_tourism` | 自治体・観光公式ページ |
| `public_directory` | 中立的な公開ディレクトリや紹介ページ |
| `manual_editorial_seed` | PoC段階の手動仮説。自動処理では低confidence扱い |

## 生成されるシグナル

例:

```json
{
  "key": "style.sanuki_influenced",
  "weight": 0.9,
  "confidence": 0.84,
  "source": "external_signal",
  "sourceTypes": ["official_tourism"],
  "evidence": ["term:讃岐"]
}
```

`weight` は推薦計算上の効き、`confidence` は根拠語の信頼度です。
公式サイトや自治体ページは高め、一般公開ディレクトリは控えめに扱います。

## 定期化の扱い

初期段階では cron を設定しません。
外部ページの構造変更、権利・利用条件、誤抽出のリスクがあるため、まずは手動実行の report-only workflow で変化を確認します。
安定後に、対象ソースを限定した低頻度更新を検討します。
