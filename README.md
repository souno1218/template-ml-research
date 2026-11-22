# プロジェクト名

<このプロジェクトの目的を1〜2文で>

AI (Claude) が実装・実験・記録の主体となって進める、機械学習 (PyTorch) の研究用テンプレートです。
AI への指示の入口は [CLAUDE.md](CLAUDE.md) (同じ内容の [AGENTS.md](AGENTS.md))、運用ルールは [docs/rules/](docs/rules/) にあります。

## セットアップ

```bash
uv sync
uv run pre-commit install
```

最初に `pyproject.toml` の `name`、`src/project_name/` の名前、この README の題を、プロジェクト名に合わせて直します。

## 研究の流れ

1. 問いを `.okf/questions/` に書き、評価一式を `bench/suites/v1/` に作る (`kind: bench` の施策)。
2. 施策を提案する: `uv run scripts/new_experiment.py --title "..." --slug ... --kind model --question Q1 --by claude/<model>`。
   Proposal (仮説・予測・合格の基準・予算) を書いて PR を作り、人間が「承認」とコメントする。
3. 実装して回す: `uv run scripts/sweep.py experiments/E0001-*/sweep.toml` (push 済みの commit からだけ動く)。
4. 集計して記録する: `uv run scripts/collect.py E0001`、Experiment を書く。
5. 判定する: Decision を書き、人間が PR をマージして確定する。不採用・保留も記録は main に残す。

詳しくは [docs/rules/lifecycle.md](docs/rules/lifecycle.md)。

## 持続可能性のための仕組み

| 仕組み | 何を防ぐか | どこで |
|---|---|---|
| 評価一式の版とハッシュ | AI や人が評価を変えて数字を良く見せる | `bench/suites/`、`lab/suite.py`、テスト、`run.py`、hooks |
| push 済みの commit からだけ実行 | 再現できない結果 | `scripts/run.py` |
| 人間に渡すのは 1 行 (pueue のタスク) | 貼り間違い、結果の push 忘れ | `scripts/launch.py` |
| 実行の記録 (`runs/<run_id>/meta.json`) | どの commit・seed・環境の数字か分からない | `scripts/run.py`、`collect.py` |
| 事前登録 (予測と合格の基準) | 結果を見てからの解釈の後付け | Proposal、テスト |
| 試して採用しなかったことの一覧 | 同じ失敗を繰り返す | `.okf/proposals/index.md` (自動生成) |
| ルールの版と検査 | 古いルールのまま進む、文書の形が崩れる | `docs/rules/VERSION`、`tests/test_rules.py` |
| Claude Code の hooks | 評価・ルールの書き換え、main への push、取り返しのつかない git の操作、現在地の読み忘れ | `.claude/settings.json`、`scripts/hooks/` |
| 現在地の 1 枚 | チャットをまたいで文脈が消える | `.okf/status.md` |

## 開発

```bash
uv run ruff check .        # lint
uv run ruff format .       # 整形
uv run ty check            # 型チェック
uv run pytest              # テスト (ルールの検査を含む)
uv run python tools/okf/validate.py .okf --strict
```

## ドキュメント

知識ドキュメント (問い・提案・実験・判断・設計・参照・現在地) は `.okf/` にあります (Open Knowledge Format v0.3)。
入口は [.okf/index.md](.okf/index.md)、書き方は [docs/rules/okf.md](docs/rules/okf.md)。
