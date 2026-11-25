# Decision

`uv run scripts/index.py` が作る (手で編集しない)。

* [OKF を知識ドキュメントの標準にする](adopt-okf.md) - 知識ドキュメントを Open Knowledge Format v0.3 のバンドルとして .okf/ に置く判断。
* [AI 駆動研究の汎用の枠組みを入れる](adopt-research-framework.md) - execSR で育てた施策の流れ・評価の凍結・実行の強制・hooks を、PyTorch の研究に共通の枠組みとしてテンプレートに入れ、Question と Status の type を足す判断。
* [AI への指示の本文を AGENTS.md に書き、CLAUDE.md はそれを読み込むだけにする](agents-md-as-entry.md) - Claude 以外の AI ツールでも同じ規約を読めるよう、入口の文書の本文を AGENTS.md に置き、CLAUDE.md は @AGENTS.md の 1 行にする判断。
* [長い計算は pueue で回し、人間に渡すのは 1 行にする](run-long-jobs-with-pueue.md) - 人間のマシンでの長い計算を tmux ではなく pueue のタスクとして回し、commit の照合から結果の push までを scripts/launch.py の 1 行にまとめる判断。
