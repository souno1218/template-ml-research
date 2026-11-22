---
type: Decision
title: 長い計算は pueue で回し、人間に渡すのは 1 行にする
description: 人間のマシンでの長い計算を tmux ではなく pueue のタスクとして回し、commit の照合から結果の push までを scripts/launch.py の 1 行にまとめる判断。
tags: [running, process]
status: stable
generated: { by: "claude/opus-5-5", at: "2026-11-22T18:55:00Z" }
sources:
  - id: pueue
    resource: https://github.com/Nukesor/pueue
    title: pueue (コマンドの順番待ちと裏での実行の道具)
---

# 判断

人間のマシンで回す長い計算は、pueue のタスクとして回す。[^pueue] AI が人間に渡すのは、commit を照合して
`scripts/launch.py` を呼ぶ 1 行だけにする。タスクは実行・集計・(必要なら) モデルの保管・結果の push までを行う。
手順は [docs/rules/running.md](../../docs/rules/running.md) にある。

# 理由

- tmux は、コピペに特別な操作が要り、抜け方・戻り方を覚える必要があって使いにくかった (ユーザーの判断、2026-11-22)。
- pueue は Mac・Linux・Windows で動き、画面を乗っ取らないので、コピペも履歴も普通の端末のまま使える。端末を閉じても計算は続き、複数の計算は順番待ちになる。[^pueue]
- 複数行のコマンドを貼る方式は、途中の行を貼り忘れる・結果の push を忘れることがあった。1 行にまとめ、終わりの処理をタスクに含めた。

# 影響

- ルールの版を 2 に上げた。
- pueue を入れられないマシンのために、`--detach` (端末から切り離したプロセスで回す) を残した。

[^pueue]: pueue
