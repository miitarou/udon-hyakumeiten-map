# External Signals PoC

`external_signals` は、「この店が好きなら」推薦を少しだけ実店舗文脈に寄せるための補助データです。
実行時にLLM/APIを呼ばず、GitHub Actions上でも再現できる定型処理だけで生成します。

## 方針

- 外部ページ本文、口コミ本文、点数、写真、SNS投稿、ユーザー名は保存しません。
- 保存するのは、人間が確認した短い根拠語だけです。
- 根拠語は `scripts/generate_external_signals.py` の固定辞書で既存タグに変換します。
- 生成された `data/external_signals.json` を `data/recommendation_tags.json` に取り込みます。
- 推薦UIでは、店舗評価ではなく探索補助として扱います。

## 台帳拡張の考え方

外部情報は2段階で管理します。

1. `data/external_signal_backlog.json`
   - 未登録店舗の作業キューです。
   - 選出回数、カテゴリ、地域から優先順位を付けます。
   - アプリや推薦計算では使いません。
2. `data/external_source_registry.json`
   - 人間が外部ソースと短い根拠語を確認したレビュー台帳です。
   - ここへ昇格したものだけが `external_signals` として推薦タグに取り込まれます。

補助的に `data/external_source_review_log.json` も使います。
これは「探したが昇格しなかった」「次回再確認が必要」といった作業履歴を残すためのログで、アプリや推薦計算では使いません。
`external_source_registry.json` には、レビュー済みで推薦タグ化してよいと判断したソースだけを入れます。

初期PoCでは、殿堂入り相当店舗から固定seedで20店舗を抽出し、`external_source_registry.json` に登録しました。

- seed: `20260512`
- うどん殿堂入りしきい値: 6回以上
- そば殿堂入りしきい値: 4回以上
- 対象件数: 20件

残り店舗は `external_signal_backlog.json` を見ながら、選出回数上位、殿堂入り相当、推薦ゴールデンセット対象、情報量の多い店舗から順次レビューします。

## 生成フロー

```bash
python3 scripts/generate_external_signal_backlog.py
python3 scripts/generate_external_signals.py
python3 scripts/generate_recommendation_tags.py
python3 scripts/check_data_quality.py
python3 scripts/evaluate_recommendations.py > build/recommendation-report.md
```

`--check` を付けると、生成済みファイルが古くないかだけを確認できます。

```bash
python3 scripts/generate_external_signal_backlog.py --check
python3 scripts/generate_external_signals.py --check
```

## 1店舗あたりのレビュー手順

1. `external_signal_backlog.json` から次の対象を選ぶ
2. 公式サイト、自治体・観光公式ページ、中立的な公開ディレクトリを探す
3. ページ本文は保存せず、推薦に効く短い根拠語だけを `evidenceTerms` に登録する
4. `sourceType`, `sourceUrl`, `sourceTitle`, `lastCheckedAt`, `reviewStatus` を記録する
5. 生成・検証コマンドを実行し、推薦レポートの悪化がないか確認する

昇格しない場合でも、`external_source_review_log.json` に `outcome: "deferred"` または `outcome: "no_allowed_source_found"` として記録します。
これにより、同じ店舗を何度もゼロから探し直さず、次回は保留理由を踏まえて再確認できます。

ページが閉鎖・移転した場合、既存の推薦は即座には壊れません。
ただし `sourceUrl` の死活や `lastCheckedAt` の古さを定期的に見直し、古いものは `reviewStatus` を `needs_review` などに変更します。

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

推薦時は、外部シグナルで補強された体験タグをスコア上でごく軽く加点し、理由文の候補としても優先します。一方で、AI推定だけの弱いタグはスコア計算には使いますが、理由文には出しすぎない方針です。

## 定期化の扱い

初期段階では cron を設定しません。
外部ページの構造変更、権利・利用条件、誤抽出のリスクがあるため、まずは手動実行の report-only workflow で変化を確認します。
安定後に、対象ソースを限定した低頻度更新を検討します。
