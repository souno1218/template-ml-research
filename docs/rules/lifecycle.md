# 施策の進め方

施策は、1 つの問いに答えるための実験の単位。ID・ブランチ・Proposal・Experiment・判定を必ず持つ。

```
提案 (proposed) → 承認 (approved) → 実行 (running) → 判定 (adopted / rejected / parked)
```

| 置き場所 | 中身 |
|---|---|
| `.okf/proposals/Exxxx-<slug>.md` | 提案。施策の状態 (`state`) はここの frontmatter に書く |
| `.okf/experiments/Exxxx-<slug>.md` | 結果・予測との比較・考察・判定の案 |
| `.okf/decisions/Exxxx-<slug>.md` | 確定した判定 (採用・不採用・保留) と理由 |
| `experiments/Exxxx-<slug>/` | `configs/` (案ごとの設定)、`code/` (試作)、`sweep.toml`、`results/` (集計) |

## 1. 提案

```bash
uv run scripts/new_experiment.py --title "学習率を上げる" --slug larger-lr \
    --kind model --question Q1 --by claude/<model>
```

ブランチ `exp/E0001-larger-lr` に切り替わり、上の 3 つ (Decision 以外) がテンプレートから作られる。
Proposal の frontmatter と本文を埋める。frontmatter と見出しはテストで検査する (`src/project_name/lab/proposals.py`)。

| 項目 | 内容 |
|---|---|
| `id` | `E` + 4 桁 |
| `state` | `proposed` / `approved` / `running` / `adopted` / `rejected` / `parked` |
| `status` (OKF) | `state` が `proposed` の間は `draft`、それ以外は `stable` |
| `kind` | `model` (モデル・学習・推論の変更) / `bench` (評価一式の変更) / `infra` (道具・ルールの変更) |
| `question` | `.okf/questions/` の問いの番号 (`Q1` など)。`infra` は `"-"` |
| `branch` | `exp/<ファイル名>` |
| `rules_version` | 提案を書いたときの `docs/rules/VERSION` |
| `suite` | 測る評価一式の版 (`v1` など)。`infra` は `"-"` |
| `baseline` | 比べる相手の設定 |
| `variants` | 並べる案の名前の一覧 (`experiments/<施策>/configs/<案>.toml` と対応) |
| `tier` | 目指す段階 (`smoke` / `screen` / `confirm`、`evaluation.md`) |

本文に必ず書くこと (見出しはテンプレートのまま):

- **問いと仮説**: 何が起きると考えるか。根拠にした過去の結果を引く。`.okf/proposals/index.md` の「試して採用しなかったこと」に同じ案があれば、その理由に答える。
- **変えること**: 基準線から変えるのは何か。案ごとに。
- **予測**: 計算の前に、結果の見込みを数字の範囲で書く。後から都合のよい解釈を付けないため。
- **合格の基準**: どの評価一式のどの指標が、どれだけ変われば、次の段階に進むか・採用するか。
- **予算**: 段階と、見込みの計算時間とマシン。

書いたら `.okf/log.md` に 1 行足し、commit・push し、Pull Request (base: main) を作る。PR の題は `E0001: <title>`。

## 2. 承認

人間が PR を読み、「承認」とコメントする。AI は `state: approved`、`status: stable` にして commit し、着手する。
承認の前に計算を回してよいのは `smoke` (動くかどうかの確認) だけ。

## 3. 実行

- 計算は `running.md` に従う。始めたら `state: running` にし、`.okf/status.md` の「実行中の計算」に書く。
- 結果が出たら `scripts/collect.py` で集計を `results/` に写し、Experiment を書いて commit・push する。
- 途中で計画を変えるとき (案を足す、段階を上げる) は、Proposal の「変更」に日付つきで追記する。合格の基準は後から緩めない。

## 4. 判定

AI が Experiment の「判定の案」に案ごとの判定と理由を書き、Proposal の `state` を判定の案に書き換え、
Decision (`.okf/decisions/Exxxx-<slug>.md`) を書いて push する。Decision の `description` は判定を 1 文で書く
(`.okf/proposals/index.md` の「判定」の列に出る)。人間が PR をマージした時点で確定する。
判定に同意しないときは、人間が PR にコメントし、AI が直す。

| 判定 | 本体のコード | 記録 (Proposal / Experiment / Decision / results) | ブランチ |
|---|---|---|---|
| 採用 (`adopted`) | `src/project_name/` に移し、`.okf/architecture/` を更新する。基準線を測り直して `.okf/status.md` に反映する | main へ | マージ後に削除 |
| 不採用 (`rejected`) | main に入れない | **main へ** | `archive/Exxxx` のタグを付けてから削除 |
| 保留 (`parked`) | main に入れない | main へ。保留の理由と再開の条件を書く | `archive/Exxxx` のタグを付けてから削除 |

不採用・保留の施策も、記録は main に残す。不採用のときは、マージする PR から `code/` 以外のコード変更を外す (本体を汚さない)。
採用の判定には、`confirm` 段階の結果が必要 (`evaluation.md`)。

## 5. 1 つの施策に複数の案を並べる

同じ問いに対する候補は、1 つの施策の中の案として並べる。ブランチは分けない。

- 案ごとに `configs/<案>.toml` を 1 つ置く (基準線の設定を `inherit` し、違うところだけ書く)。
- `sweep.toml` に、どの案を何 seed 回すかを書く。
- 判定は案ごとに出す。採用した案のコードだけを本体に移す。
- 案の組み合わせも、案の 1 つとして並べる。

ブランチ (= 施策) を分けるのは、問いや仮説が別で、採用・不採用が互いに独立に決まるとき。

## 6. 別のプロジェクトから持ち込むとき

別のプロジェクトでの結果は、Proposal の「問いと仮説」に書くだけにする。採用の判断は、このリポジトリの評価でだけ行う。
