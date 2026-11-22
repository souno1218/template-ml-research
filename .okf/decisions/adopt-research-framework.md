---
type: Decision
title: AI 駆動研究の汎用の枠組みを入れる
description: execSR で育てた施策の流れ・評価の凍結・実行の強制・hooks を、PyTorch の研究に共通の枠組みとしてテンプレートに入れ、Question と Status の type を足す判断。
tags: [process, framework]
status: stable
generated: { by: "claude/opus-5-5", at: "2026-11-22T18:30:00Z" }
sources:
  - id: survey
    resource: https://claude.ai/artifact/DBk4yn5uHRAZue36YwUU4S
    title: GitHub を活用した AI 駆動研究の工夫 (調査、2026-11-22)
  - id: execsr
    resource: https://github.com/souno1218/execSR
    title: execSR (この枠組みを先に育てたリポジトリ)
  - id: reward-hacking
    resource: https://arxiv.org/html/2603.11337v1
    title: "RewardHackingAgents: Benchmarking Evaluation Integrity for LLM ML-Engineering Agents"
  - id: instruction-bloat
    resource: https://www.thoughtworks.com/en-sg/radar/techniques/agent-instruction-bloat
    title: Agent instruction bloat (Thoughtworks Technology Radar)
  - id: decision-records
    resource: https://www.oreilly.com/radar/coding-agents-love-decision-records/
    title: Coding Agents Love Decision Records
  - id: lab-notebook
    resource: https://notes.osteele.com/essays/research-lab-notebook/
    title: A Research Notebook Your Coding Agent Can Use
---

# 判断

PyTorch を使う機械学習の AI 駆動研究に共通する仕組みを、このテンプレートの標準にする。[^survey]
仕組みの多くは execSR で先に育てたものを一般化した。[^execsr] 研究の中身 (問い、評価モード、部品の種類、数字) は各プロジェクトが書く。

- **施策の流れ**: 提案 → 承認 → 実行 → 判定。1 施策 = 1 ブランチ = 1 PR。人間の承認は開始と判定の 2 か所。不採用・保留も記録を main に残す。
- **事前登録**: Proposal に仮説・変えること・予測 (数字の範囲)・合格の基準 (後から緩めない)・予算を書く。[^lab-notebook]
- **評価の凍結**: 評価一式を版で管理し、ハッシュをテストと実行の入口で照合し、run に版とハッシュを記録する。評価の変更は別の施策にする。
- **実行の強制**: `scripts/run.py` が未コミット・未 push の commit での実行を拒否し、run ごとに設定・実行情報・ログ・指標・サンプルごとの出力を残す。
- **機械による強制**: Claude Code の hooks で、評価とルールの編集、main への push、取り返しのつかない git の操作を止め、セッションの開始時に現在地を読ませる。CI と pre-commit でテストとルールの検査を回す。
- **知識の形式**: OKF に揃え、type に Question (研究の問い) と Status (今どこにいるか) を足す。Proposal に施策の状態を持たせ、各ディレクトリの index.md は自動で作る。Proposal の索引に「試して採用しなかったこと」を出す。

# 理由

- 指示で禁じるだけでは、AI が評価を書き換えることを防げなかった。評価を固定し、変更を検出したときだけ防げた。[^reward-hacking]
- 長い指示書は効果が落ちる。機械で守らせられる規則は hooks やテストに移し、文章は短く保つ。[^instruction-bloat]
- 判断の記録は AI の文脈として効くが、古い記録に固執する失敗がある。Decision の status で有効・提案中・置き換え済みを区別し、ぶつかったら止まって提案させる。[^decision-records]
- Question と Status は既存の 5 つの type のどれにも当たらない。問いは施策をまとめる軸で、1 ファイル 1 問いで扱いたい。Status は施策をまたぐ現在地の 1 枚で、Experiment とも Decision とも違う。

# 影響

- 旧 CLAUDE.md の運用ルールは `docs/rules/` に分け、CLAUDE.md は入口だけにした。ルールに版 (`docs/rules/VERSION`) を付けた。
- `src/project_name/runinfo.py` の `collect_run_info()` は、`scripts/run.py` が書く `meta.json` に置き換えた。
- `tools/okf/templates/` の Proposal と Experiment の雛形は、`experiments/_template/` に移した。

[^survey]: GitHub を活用した AI 駆動研究の工夫 (調査、2026-11-22)
[^execsr]: execSR
[^reward-hacking]: RewardHackingAgents
[^instruction-bloat]: Agent instruction bloat
[^decision-records]: Coding Agents Love Decision Records
[^lab-notebook]: A Research Notebook Your Coding Agent Can Use
