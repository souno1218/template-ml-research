# 施策の進め方

施策は、1 つの問いに答えるための実験の単位。ID・ブランチ・提案書・判定を必ず持つ。

```
提案 (proposed) → 承認 (approved) → 実行 (running) → 判定 (adopted / rejected / parked)
```

Issue は、施策になる前のアイデアや問いの置き場として使う。施策にするときは提案書を書き、PR の本文に `Refs #N` を付ける。長く残る問いは `docs/questions.md` に Q 番号で書く。

## 1. 提案

```bash
uv run scripts/new_experiment.py --title "縦方向のアテンションを変える" --slug vertical-attn --kind model --question Q2
```

次のものが作られ、ブランチ `exp/E0007-vertical-attn` に切り替わる。

- `.okf/proposals/E0007-vertical-attn.md` — 提案書 (OKF の Proposal)
- `experiments/E0007-vertical-attn/` — `configs/`、`code/`、`results/`

提案書の frontmatter と本文を埋める。frontmatter はテストで検査する。

| キー | 内容 |
|---|---|
| `x-id` | `E` + 4 桁 |
| `x-kind` | `model` (モデル・学習・推論の変更) / `bench` (評価一式の変更) / `infra` (道具・ルールの変更) |
| `x-phase` | `proposed` / `approved` / `running` / `adopted` / `rejected` / `parked` |
| `x-question` | `docs/questions.md` の問いの番号。なければ `-` |
| `x-branch` | `exp/<ID>-<slug>` |
| `x-rules-version` | 提案を書いたときの `docs/rules/VERSION` |
| `x-suite` | 測る評価一式の版 (`v1` など)。`infra` は `-` |
| `x-baseline` | 比べる相手の設定 (`experiments/.../configs/...`) |
| `x-variants` | 並べる案の名前の一覧 (`configs/<案>.toml` と対応) |
| `x-tier` | 目指す段階 (`benchmark.md`) |

OKF の `status` は、提案中は `draft`、承認後は `stable` にする。

本文に必ず書くこと: **仮説と根拠** / **変えること** / **合格の基準** / **予算**。

書いたら commit・push し、Pull Request (base: main) を作る。PR の題は `E0007: <title>`。

## 2. 承認

人間が PR を読み、「承認」とコメントする。AI は `x-phase: approved`、`status: stable` にして commit し、着手する。
承認の前に計算を回してよいのは、最も小さい段階 (smoke、動くかどうかの確認) だけ。

## 3. 実行

- 計算は `running.md` に従う。始めたら `x-phase: running` にし、`docs/status.md` の「実行中」に書く。
- 結果が出たら `scripts/collect.py` で集計を `results/` に写し、Experiment (`.okf/experiments/E0007-*.md`) を書いて commit・push する。
- 途中で計画を変えるとき (案を足す、段階を上げる) は、提案書の本文に「変更」として日付つきで追記する。**合格の基準は後から緩めない。**

## 4. 判定

AI が Experiment の末尾に案ごとの判定と理由を書き、提案書の `x-phase` を判定の案 (`adopted` / `rejected` / `parked`) に書き換えて push する。判定は Decision (`.okf/decisions/NNNN-*.md`) にも書く。
人間が PR をマージした時点で確定する。同意しないときは、人間が PR にコメントし、AI が直す。

| 判定 | 本体のコード | 記録 | ブランチ |
|---|---|---|---|
| 採用 | `src/` に移し、Architecture を更新する。基準線を測り直す | main へ | マージ後に削除 |
| 不採用 | main に入れない | **main へ** (提案書・Experiment・Decision・results) | `archive/Exxxx` のタグを付けてから削除 |
| 保留 | main に入れない | main へ。理由と再開の条件を書く | `archive/Exxxx` のタグを付けてから削除 |

不採用・保留の施策も、記録は main に残す。そのとき、マージする PR から `experiments/Exxxx-*/code/` 以外のコード変更を外す。

## 5. 1 つの施策に複数の案を並べる

同じ問いに対する候補は、1 つの施策の中の案として並べる。ブランチは分けない。

- 案ごとに `configs/<案>.toml` を 1 つ置き、判定は案ごとに出す。採用した案のコードだけを本体に移す。
- ブランチ (= 施策) を分けるのは、問いや仮説が別で、採用・不採用が互いに独立に決まるとき。

## 6. 別のプロジェクトから持ち込むとき

別のプロジェクトでの結果は、提案書の「仮説と根拠」に書くだけにする。採用の判断は、このリポジトリの評価でだけ行う。
