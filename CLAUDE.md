# AI の作業の入口

このリポジトリは、AI (Claude) が実装・実験・記録の主体となって進める研究用のリポジトリです。
**作業を始める前に、必ず次の順に読んでください。** 読まずに始めた作業は無効です。

1. このファイル
2. `docs/rules/ai.md` (AI の作業規則)
3. `docs/status.md` (今どこにいるか)
4. 作業の種類に応じて:
   - 施策を提案・実行する → `docs/rules/lifecycle.md`、`docs/rules/benchmark.md`、`docs/questions.md`
   - 計算を回す・回してもらう → `docs/rules/running.md`、`docs/machines.md`
   - コードを書く → `docs/rules/code.md`
   - 知識ドキュメント (`.okf/`) を書く → `docs/rules/okf.md`
5. 対象の施策の提案書 (`.okf/proposals/Exxxx-*.md`)

読み終えたら、最初の返答の 1 行目で「ルール v<`docs/rules/VERSION` の値> を読んだ。対象: <施策 ID か作業の内容>」と報告してから作業します。

## 絶対ルール

1. **リポジトリに書いていないことは、決まっていない・起きていない。** 決めたことは `.okf/decisions/` に、結果は施策の Experiment (`.okf/experiments/`) に、その場で書いて commit する。
2. **本体 (`src/`) には、採用と判定された施策のコードだけを入れる。** 試作は `experiments/Exxxx-*/code/` に置き、registry で差し込む。
3. **1 つの施策の中で、評価 (`bench/`) とルール (`docs/rules/`) を変えない。** 変えたいときは、それ自体を別の施策として提案する。
4. **計算は、GitHub に push 済みの commit からだけ回す** (`scripts/run.py` が強制する)。
5. **main に直接 push しない。** main に入るのは、人間がマージした Pull Request だけ。人間の承認は「施策の開始」と「採用の判定」の 2 か所。

## 開発環境とコマンド

- Python は uv で管理する。lint と整形は ruff、型検査は ty、テストは pytest。
- 変更を終える前に、次をすべて通す。pre-commit と CI でも同じものが動く。

```bash
uv run ruff check . && uv run ruff format --check . && uv run ty check && uv run pytest
uv run python tools/okf/validate.py .okf --strict      # OKF の検証
uv run scripts/new_experiment.py --title "..." --slug ... --kind model   # 施策の提案
```

- 最初に `pyproject.toml` の `name`、`src/project_name/` の名前、README の題を、プロジェクト名に合わせて直す。
