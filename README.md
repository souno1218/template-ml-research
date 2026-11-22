# プロジェクト名

<このプロジェクトの目的を1〜2文で>

## セットアップ

```bash
uv sync
uv run pre-commit install
```

## 実行

```bash
# <実行コマンド>
```

## 実験の流れ

1. 施策を提案する: `uv run scripts/new_experiment.py --title "..." --slug ... --kind model`(提案書・施策ディレクトリ・ブランチが作られる)。提案書を埋めて PR を作り、人間が「承認」とコメントする
2. 実装・実験する: `uv run scripts/run.py E0000 <案> --seed 0 -- <コマンド>`(push 済みの commit からだけ回せる)→ `uv run scripts/collect.py E0000` → Experiment に結果と判定の案を書く
3. 人間が PR をマージして、採用・不採用・保留が確定する

規約は [CLAUDE.md](CLAUDE.md) と `docs/rules/` を参照。GitHub の初期設定は [docs/setup.md](docs/setup.md)。

## 開発

```bash
uv run ruff check .        # lint
uv run ruff format .       # 整形
uv run ty check            # 型チェック
uv run pytest              # テスト
```

## ドキュメント

知識ドキュメント（提案・判断・実験・設計・参照）は `.okf/` にあります（Open Knowledge Format）。入口は [.okf/index.md](.okf/index.md)、規約は [CLAUDE.md](CLAUDE.md) を参照。
