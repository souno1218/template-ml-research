---
type: Experiment
title: "{{id}}: {{title}} の結果"
description: <何を比べ、何が分かったかを1文で。計算の後に書く。>
tags: []
generated: { by: "{{by}}", at: "{{at}}" }
sources:
  - id: summary
    resource: ../../experiments/{{stem}}/results/summary.md
    title: "{{id}} の結果の集計 (scripts/collect.py)"
---

# 対応する提案

[Proposal](../proposals/{{stem}}.md)

# 実行情報

各 run の commit・seed・マシン・ライブラリの版・評価一式のハッシュは、`experiments/{{stem}}/results/<案>/s<seed>/meta.json`
にある (`scripts/run.py` が記録し、`scripts/collect.py` が写す)。dev の run と dirty な run は採用の根拠にしない。

# 結果

<集計の表から、判定に使う数字だけを、95% 区間つきで写す。>[^summary]

| 案 | 指標 | 値 (95% 区間) |
|---|---|---|
| <案> | <指標> | <値> |

# 予測との比較

<Proposal の「予測」と比べて、当たったか外れたか。外れた理由の見立て。>

# 考察

<結果から言えること。言えないこと。次にやること。>

# 判定の案

<案ごとに 採用 / 不採用 / 保留 と理由。人間が PR をマージした時点で確定し、Decision に写す。>

[^summary]: {{id}} の結果の集計
