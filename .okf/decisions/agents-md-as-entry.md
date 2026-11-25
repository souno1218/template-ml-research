---
type: Decision
title: AI への指示の本文を AGENTS.md に書き、CLAUDE.md はそれを読み込むだけにする
description: Claude 以外の AI ツールでも同じ規約を読めるよう、入口の文書の本文を AGENTS.md に置き、CLAUDE.md は @AGENTS.md の 1 行にする判断。
tags: [process, rules]
status: stable
generated: { by: "agent:claude", at: "2026-11-25T10:44:41Z" }
sources:
  - id: agents-md
    resource: https://agents.md/
    title: AGENTS.md (AI エージェント向けの指示を置く共通のファイル)
  - id: claude-memory
    resource: https://code.claude.com/docs/en/memory
    title: Claude Code の CLAUDE.md と @ による読み込み
---

# 判断

AI への指示の入口の本文は `AGENTS.md` に書く。`CLAUDE.md` は `@AGENTS.md` の 1 行だけにする。
`generated.by` と `--by` は、使ったツールの名前で `<tool>/<model>` と書く。

# 理由

- Claude 以外の AI ツールでも、このリポジトリで作業できるようにする (ユーザーの判断、2026-11-25)。
- `AGENTS.md` は、多くの AI ツールが読む共通のファイル名である。[^agents-md]
- Claude Code は、`CLAUDE.md` に書いた `@<パス>` のファイルを読み込む。[^claude-memory] そのため本文を 1 か所にでき、
  これまでの「2 つのファイルを同じ内容に保つ」運用 (`cp CLAUDE.md AGENTS.md` とテスト) が要らなくなる。

# 影響

- ルールの版を 3 に上げた。
- `tests/test_rules.py` は、`CLAUDE.md` が `@AGENTS.md` だけであることと、`AGENTS.md` が指すファイルがあることを確かめる。
- `.claude/settings.json` の hooks が効くのは Claude Code だけである。ほかのツールでは、pre-commit・CI・`scripts/run.py` の検査だけが機械で止める。`AGENTS.md` にそう書いた。

[^agents-md]: AGENTS.md
[^claude-memory]: Claude Code の CLAUDE.md と @ による読み込み
