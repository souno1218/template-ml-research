# 評価一式

`bench/suites/<版>/` に、評価データと `suite.toml` (ファイルと sha256) を置く。書式は `src/project_name/lab/suite.py`、
手順は `docs/rules/evaluation.md`。一度 commit した版は変更せず、変えるときは `kind: bench` の施策で次の版を作る。
