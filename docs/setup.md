# 初期設定のチェックリスト

テンプレートからリポジトリを作ったあとに、GitHub の画面で行う設定。

- [ ] Settings → Rules → Rulesets で、`main` に次を設定する: Pull Request を必須にする / ステータスチェック `check` (CI) を必須にする / 直接 push と force push を禁止する。
- [ ] Settings → General で「Automatically delete head branches」を有効にする。
- [ ] GPU のあるマシンで、`git clone` と `gh auth login` を済ませる (`docs/rules/running.md`)。
- [ ] `pre-commit install` を実行する。
- [ ] `pyproject.toml` の `name`、`src/project_name/`、README の題をプロジェクト名に直す。
- [ ] `docs/questions.md` に最初の問いを書く。`bench/README.md` に評価の段階の規模を書く。
