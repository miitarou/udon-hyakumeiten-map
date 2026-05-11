# 推薦タグ設計メモ

このドキュメントは、`data/recommendation_tags.json` を使って、実行時にLLMや外部APIを呼ばずに店舗推薦を行うための設計方針をまとめたものです。

推薦タグは、店舗説明を断定するためのデータではなく、店舗間の近さを計算するための探索補助データです。

## 基本方針

- 推薦実行時にLLM/APIを呼ばない。
- 推薦タグは静的JSONとして保持する。
- 店舗本体データ `data/udon.json` / `data/soba.json` とは分離する。
- 事実タグと推定タグを明確に分ける。
- 推定タグは `weight` と `confidence` を必ず持つ。
- 低確度タグは内部スコアには使ってよいが、理由文では断定的に表示しない。
- 営業時間、価格、混雑、予約可否など変動しやすい情報は原則タグ化しない。

## タグ数の考え方

現時点のタグ定義は103種類です。

これは完成上限ではなく、初期版のタグ辞書です。ただし、タグは無制限に増やさず、次の条件を満たす場合だけ追加します。

- 複数店舗にまたがって意味がある。
- 推薦結果を実際に変える。
- UI上の理由表示にも使える。
- 既存タグでは表現できない。
- 低確度の思いつきではない。

1店舗だけにしか使わないタグは、原則として追加しません。必要なら個別メモではなく、既存タグの `weight` / `confidence` 調整で吸収します。

## タグの種類

タグは自由文ではなく、定型キーで管理します。

例:

```text
genre.udon
genre.soba
pref.osaka
region.west
selection.hall_of_fame_relative
style.sanuki_influenced
texture.koshi_strong
dish.duck
scene.destination
mood.traditional
lineage.yabu
```

大分類は以下です。

| 接頭辞 | 用途 | 例 |
| --- | --- | --- |
| `genre.*` | ジャンル | `genre.udon`, `genre.soba` |
| `region.*` | 百名店カテゴリ上の地域 | `region.east`, `region.west`, `region.kagawa` |
| `pref.*` | 都道府県 | `pref.osaka`, `pref.tokyo` |
| `macro_area.*` | 広域地域 | `macro_area.kansai`, `macro_area.kanto` |
| `selection.*` | 選出履歴 | `selection.repeat`, `selection.hall_of_fame_relative` |
| `status.*` | 営業状態 | `status.open`, `status.closed_or_moved` |
| `style.*` | 店舗・系統の方向性 | `style.sanuki_influenced`, `style.edomae_soba` |
| `texture.*` | 麺・食感の方向性 | `texture.koshi_strong`, `texture.aroma_focused` |
| `dish.*` | 看板料理・料理系統 | `dish.kamaage`, `dish.duck` |
| `scene.*` | 利用シーン | `scene.solo_lunch`, `scene.destination` |
| `mood.*` | 雰囲気 | `mood.traditional`, `mood.modern` |
| `lineage.*` | そば系譜などの連想 | `lineage.yabu`, `lineage.sarashina` |

## source の意味

各タグには `source` を持たせます。

| source | 意味 | 信頼度の考え方 |
| --- | --- | --- |
| `data` | 既存JSONから直接得られる事実 | 原則 `confidence=1.0` |
| `name_keyword` | 店名キーワードからの推定 | 強め。ただし誤検出に注意 |
| `selection_prior` | 選出回数・殿堂入り相当からの推定 | 中程度 |
| `regional_prior` | 地域性からの推定 | 中〜弱 |
| `model_prior` | ジャンル一般からの弱い推定 | 弱め |

例:

```json
{
  "key": "style.sanuki_influenced",
  "weight": 0.9,
  "confidence": 0.84,
  "source": "name_keyword",
  "evidence": ["name_keyword:讃岐"]
}
```

## weight と confidence

`weight` と `confidence` は役割が違います。

`weight` は、そのタグが推薦計算上どれくらい重要かです。

`confidence` は、そのタグ付け自体をどれくらい信用するかです。

単純には、以下をタグの有効強度として扱います。

```text
有効強度 = weight × confidence
```

例:

```text
style.sanuki_influenced
0.90 × 0.84 = 0.756
```

これは推薦上かなり強い特徴です。

一方で:

```text
scene.solo_lunch
0.52 × 0.56 = 0.291
```

これは弱い補助特徴です。

整理すると以下です。

| パターン | 意味 | 推薦での扱い |
| --- | --- | --- |
| `weight`高、`confidence`高 | 重要で信頼できる特徴 | 推薦の主軸にする |
| `weight`高、`confidence`低 | 重要そうだが不確か | 弱く使う。理由文には出しにくい |
| `weight`低、`confidence`高 | 確かだが補助的 | タイブレークや軽い加点 |
| `weight`低、`confidence`低 | 弱く不確か | 内部補正用。理由文には出さない |

## タグカテゴリ係数

全タグを同じ重さで扱うと、都道府県や弱推定タグが強すぎることがあります。そのため、推薦計算時はタグの接頭辞ごとに係数を掛けます。

初期案:

| タグ種別 | 係数 | 意味 |
| --- | ---: | --- |
| `genre.*` | 1.4 | 同ジャンルを強く評価 |
| `style.*` | 1.2 | 店舗タイプ・流派の近さ |
| `texture.*` | 1.2 | 食感・味覚の近さ |
| `dish.*` | 1.1 | 看板料理の近さ |
| `lineage.*` | 1.1 | そば系譜などの近さ |
| `scene.*` | 0.8 | 利用シーンの近さ |
| `mood.*` | 0.8 | 雰囲気の近さ |
| `pref.*` | 0.7 | 近隣性 |
| `macro_area.*` | 0.45 | 広域の近さ |
| `selection.*` | 0.5 | 名店性・選出傾向の近さ |
| `region.*` | 0.45 | EAST/WEST/KAGAWAの近さ |
| `status.*` | 0 | スコアではなくフィルタに使う |

## 類似度計算

店舗Aを選んだとき、店舗Bとの類似度は共通タグを使って計算します。

タグ `t` について:

```text
A_t = A側の weight × confidence
B_t = B側の weight × confidence
categoryWeight_t = タグ接頭辞ごとの係数

共通タグ加点_t = A_t × B_t × categoryWeight_t
```

単純合計だけだと、タグ数が多い店舗ほど有利になります。そこで、コサイン類似度に近い正規化を使います。

```text
similarity(A, B) =
  共通タグ加点の合計
  /
  sqrt(Aのタグ強度合計 × Bのタグ強度合計)
```

ここでタグ強度合計は、各店舗のタグについて以下を合計します。

```text
(weight × confidence)² × categoryWeight
```

これにより、タグ数が多いだけの店舗が過剰に上位へ来ることを抑えます。

## 最終スコア

実用上は、タグ類似度だけではなく、営業状態、距離、訪問状況、推薦モードで補正します。

```text
finalScore =
  tagSimilarity
  × statusFactor
  × distanceFactor
  × visitStateFactor
  × modeFactor
```

初期案:

| 補正 | 内容 |
| --- | --- |
| `statusFactor` | 通常推薦では閉店・移転を除外。履歴探索モードなら低倍率で残す |
| `distanceFactor` | 近くで探すモードのみ強く使う |
| `visitStateFactor` | 訪問済みは減点、行きたいは軽く加点 |
| `modeFactor` | 似ている、近くで似ている、少し広げる等で係数を切り替える |

## 推薦モード

### 似ている店

選択店舗と近い体験の店舗を出すモードです。

- `genre.*`
- `style.*`
- `texture.*`
- `dish.*`
- `lineage.*`

を強めます。距離は軽い補正に留めます。

### 近くで似ている店

地理的に行きやすい候補を優先するモードです。

- 地図中心、現在地、または選択店舗からの距離を強く補正する。
- `pref.*` と `macro_area.*` をやや強める。
- タグ類似度が極端に低い店舗は近くても出しすぎない。

### 少し広げる

完全一致ではなく、探索の幅を出すモードです。

- `genre.*` の係数を少し下げる。
- `style.*`, `texture.*`, `scene.*` を重視する。
- `pref.*` より `macro_area.*` を評価する。
- 同じ趣味嗜好のまま、地域やジャンルを少しずらす。

例:

```text
讃岐系うどんが好きな人に、香川以外の関西うどんや、麺の個性が強いそばを出す。
```

### 対照候補

初期実装では後回しにします。

考え方は、中核タグを1〜2個だけ共有し、それ以外は少し違う店舗を選ぶ方式です。

例:

```text
コシ重視うどんが好きな人に、香り重視そばを出す。
```

説明が難しく、意図しないランダム推薦に見えやすいため、最初は実装しません。

## 推薦理由の生成

推薦理由もLLMなしの定型処理で生成します。

1. 共通タグのうちスコア貢献が大きいものを抽出する。
2. `confidence` が低すぎるタグを除外する。
3. `tagDefinitions` の `label` を使って短い理由文にする。

理由文に使うタグの目安:

```text
weight × confidence >= 0.45
```

例:

```text
同じ「うどん」「讃岐系の傾向」「コシ重視寄り」がおすすめ候補です。
```

```text
「大阪府」「WEST」「複数回選出」が共通しており、選出傾向もおすすめ候補です。
```

低確度タグは計算には使っても、理由文には出しません。

## Web版の初期実装仕様

Web版では、まず店舗ポップアップ内の軽量パネルとして実装しています。

- 店舗ポップアップに「この店が好きなら」ボタンを追加する。
- 押すと最大3件の候補を表示する。
- タブは3つにする。
  - 似ている
  - 近くで似ている
  - 少し広げる
- 各候補に理由タグを最大3個表示する。
- 通常推薦では閉店・移転を除外する。
- 訪問済みは減点する。
- 行きたいは少し加点する。

## 更新手順

店舗データを更新した場合は、以下を実行します。

```bash
python3 scripts/generate_data_version.py
python3 scripts/generate_recommendation_tags.py
python3 scripts/check_data_quality.py
```

iOS同梱資産も更新する場合:

```bash
npm --prefix mobile run ios:sync
```

## 注意点

- 推定タグは探索補助であり、店舗の事実説明ではありません。
- 推定タグをUIに出す場合は、低確度タグを理由文に使わないでください。
- タグを増やすより、まず既存タグの `weight` / `confidence` / 係数を調整してください。
- 誤検出例を見つけた場合は、個別JSONを手で直すのではなく、生成スクリプトのルールを修正してください。
