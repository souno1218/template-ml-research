---
type: Proposal
title: "{{title}}"
description: <この施策で何を試し、何を確かめるかを1文で。>
tags: []
status: draft
generated: { by: "{{by}}", at: "{{at}}" }
id: {{id}}
state: proposed
kind: {{kind}}
question: {{question}}
branch: exp/{{stem}}
rules_version: {{rules_version}}
suite: {{suite}}
baseline: experiments/{{stem}}/configs/baseline.toml
variants: [baseline]
tier: screen
---

# 問いと仮説

<どの問いに答えるか。何が起きると考えるか。根拠にした過去の結果を、Experiment や Decision へのリンクで引く。
同じ案が「試して採用しなかったこと」(proposals/index.md) にあれば、その判定の理由に答える。>

# 変えること

<基準線から変えるのは何か。案ごとに書く。>

| 案 | 変えること |
|---|---|
| <baseline> | <基準線そのもの> |

# 予測

<計算の前に、結果の見込みを数字の範囲で書く (例: 案 A は基準線より +1〜3 ポイント)。
差が出ない場合の解釈と、予測が外れたときに次にすることも書く。>

# 合格の基準

<どの評価一式のどの指標が、どれだけ変われば次の段階へ進むか・採用するか。後から緩めない。>

# 予算

<段階 (smoke / screen / confirm)、見込みの計算時間、マシン。>

# 中止の条件

<途中で止める条件。>

# 変更

<承認後に計画を変えたときだけ、日付つきで追記する。合格の基準は緩めない。>
