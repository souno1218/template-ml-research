# AI の作業の入口

このリポジトリは、AI エージェント (Claude Code、Codex など) が実装・実験・記録の主体となって進める、機械学習 (PyTorch) の研究用のリポジトリです。
**作業を始める前に、必ず次の順に読んでください。**

1. このファイル
2. `docs/rules/ai.md` (AI の作業規則)
3. `.okf/status.md` (今どこにいるか)
4. 作業の種類に応じて:
   - 施策を提案・実行する → `docs/rules/lifecycle.md`、`docs/rules/evaluation.md`、`.okf/questions/index.md`、`.okf/proposals/index.md`
   - 計算を回す・回してもらう → `docs/rules/running.md`、`.okf/architecture/machines.md`
   - コードを書く → `docs/rules/code.md`
   - 知識ドキュメントを書く → `docs/rules/okf.md`
5. 対象の施策の `.okf/proposals/Exxxx-*.md` と、関係する Decision (`.okf/decisions/`)

読み終えたら、最初の返答の 1 行目で「ルール v<`docs/rules/VERSION` の値> を読んだ。対象: <施策 ID か作業の内容>」と報告してから作業します。

## 絶対ルール

1. **リポジトリに書いていないことは、決まっていない・起きていない。** 決めたことは Decision に、結果は Experiment に、その場で書いて commit する。
2. **本体 (`src/project_name/`) には、採用と判定された施策のコードだけを入れる。** 試作は `experiments/Exxxx-*/code/` に置き、registry で差し込む。
3. **1 つの施策の中で、評価 (`bench/`) とルール (`docs/rules/`) を変えない。** 変えたいときは、それ自体を別の施策として提案する。
4. **計算は、GitHub に push 済みの commit からだけ回す** (`scripts/run.py` が強制する)。
5. **main に直接 push しない。** main に入るのは、人間がマージした Pull Request だけ。人間の承認は「施策の開始」と「採用の判定」の 2 か所。

3〜5 の一部は `.claude/settings.json` の hooks が機械で止める。止められたら、迂回せずに理由を読み、施策を分けるか人間に頼む。
この hooks が効くのは Claude Code だけ。ほかのツールでは止めてくれないので、上のルールを自分で守る (pre-commit・CI・`scripts/run.py` の検査は、どのツールでも効く)。

## よく使うコマンド

```bash
uv run pytest                     # テスト (ルールの検査を含む)
uv run ruff check . && uv run ruff format --check . && uv run ty check
uv run python tools/okf/validate.py .okf --strict
uv run scripts/new_experiment.py --title "..." --slug ... --kind model --question Q1 --by <tool>/<model>
uv run scripts/index.py           # .okf/*/index.md を作り直す
```

最初に `pyproject.toml` の `name`、`src/project_name/` の名前、README の題を、プロジェクト名に合わせて直す。

本文はこのファイル (`AGENTS.md`) だけに書く。`CLAUDE.md` は Claude Code がこのファイルを読み込むための 1 行だけにする。
