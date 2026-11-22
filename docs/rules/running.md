# 実行の手順

## 1. GitHub を唯一の受け渡し口にする

コードも結果も、必ず GitHub のブランチを経由する。ファイルの直接の受け渡しはしない。

- 学習・評価は `scripts/run.py` (複数なら `scripts/sweep.py`) 経由で回す。
- `run.py` は次のときに実行を拒否する:
  - 作業ツリーに未コミットの変更がある
  - HEAD が、追跡している `origin` のブランチと一致しない (push していない、または pull していない)
  - 設定に評価一式 (`[eval] suite`) があり、その評価データが `suite.toml` のハッシュと合わない
- 例外は `--dev`。動作確認用で、`runs/dev/` に書かれ、`collect.py` は集計しない。

## 2. 実行の記録

`runs/<run_id>/` に次を必ず残す (`run.py` が書く)。

| ファイル | 中身 |
|---|---|
| `config.toml` | 継承を展開した設定 |
| `meta.json` | run_id、施策、案、seed、commit、ブランチ、dirty、ルールの版、評価一式の版とハッシュ、マシン名、OS、Python とライブラリの版、デバイス、開始・終了の時刻、終了の状態 |
| `log.txt` | 標準出力と標準エラー |
| `metrics.json` | 集計の指標 (ジョブが書く) |
| `per_sample.jsonl` | サンプルごとの出力 (評価をするジョブが書く) |
| `progress.json` | 進み具合 (ジョブが一定の間隔で書く。`scripts/progress.py` が読む) |

run_id は `<日付時刻>-<施策ID>-<案>-s<seed>` (例: `20261116-213000-E0001-baseline-s0`)。
`runs/` は git の管理外。施策の結果は `scripts/collect.py Exxxx` で `experiments/Exxxx-*/results/` に写して commit する。
同じ施策・案・seed・commit で終わっていない run があれば、`run.py` はその続きから再開する (ジョブが再開に対応していれば)。

## 3. マシンごとの流れ

どのマシンを誰が回すかは `.okf/architecture/machines.md` に書く。典型は次の 2 つ。

| マシン | 誰が回すか | 流れ |
|---|---|---|
| AI が直接使えるマシン | AI | ブランチに push → その commit のまま実行 → `collect.py` → 結果を commit・push |
| 人間の GPU マシン | 人間が 1 行を貼る | AI がブランチに push し、下の形の 1 行を渡す → 人間が端末に貼る (pueue のタスクとして裏で進み、終わると集計して結果を push する) → AI が pull して Experiment を書く |

- 同じ施策の中で比べる数字は、同じ種類のマシンで出したものに限る。
- 長い計算 (目安 1 時間以上) を始めたら、`.okf/status.md` の「実行中の計算」に、マシン・コマンド・開始時刻・終わる見込みを書く。
- 進み具合は `uv run scripts/progress.py [施策 ID] [--watch 60]` で見る。5 分以上更新がない run は「止まっている?」と出る。
- 同じマシンで同時に回す本数は `sweep.toml` の `parallel` で決める。メモリの小さいマシン (Mac など) では 1 本ずつ回す。

### 人間に渡すコマンドの形

長い計算は [pueue](https://github.com/Nukesor/pueue) のタスクとして回す。pueue は Mac・Linux (WSL)・Windows で動き、
画面を乗っ取らないので、コピペも矢印キーの履歴も普通の端末のまま使える。端末を閉じても計算は続き、複数の計算は順番待ちになる。

AI は、ブランチ名・commit・施策 ID をすべて埋めた **1 行** を渡す。人間は端末に貼るだけでよい。

```bash
cd ~/<repo> && git fetch -q origin && git switch -q exp/E0001-larger-lr && git pull -q --ff-only && uv sync -q && uv run scripts/launch.py E0001 --commit abc1234
```

- `scripts/launch.py` は commit を照合し、pueue のタスクとして登録して、すぐに戻る。
  タスクは `sweep.py` → `collect.py` → (`--publish` を付けたら) `publish.py` → 結果の commit と push を順に行う。失敗したらそこで止まり、push しない。
- 見る・止める:

  | したいこと | コマンド |
  |---|---|
  | 一覧 | `pueue status` |
  | ログを追う (Ctrl-C で見るのをやめても計算は続く) | `pueue follow <タスク番号>` |
  | 終わったタスクのログ | `pueue log <タスク番号>` |
  | 止める | `pueue kill <タスク番号>` |
  | 進み具合 (ステップ数、止まっていないか) | `uv run scripts/progress.py E0001 --watch 60` |

- 同じ 1 行をもう一度貼ると、終わっていない (案, seed) だけを続きから回す。
- マシンがスリープすると止まるので、長い計算の間はスリープしない設定にする。
- pueue の入れ方 (マシンごとに 1 回): Mac は `brew install pueue`。Linux / WSL はパッケージにあれば `sudo apt install pueue`、
  なければ `cargo install --locked pueue` か [Releases](https://github.com/Nukesor/pueue/releases) のバイナリを PATH に置く。
  デーモンは `pueued -d` で起動する (`launch.py` も起動を試みる)。入れたら `.okf/architecture/machines.md` に書く。
- pueue を入れられないマシンでは、末尾に `--detach` を付けると、端末から切り離したプロセスで回す (ログは `runs/_launch/*.log`)。
- tmux は使わない (コピペしにくく、操作を覚える必要があるため)。

## 4. 学習済みモデルの保管

- 保管先は **GitHub Releases**。施策ごとに 1 つのリリース (タグ `models/E0001`) を作り、残すモデルを添付する。git には入れない。
- 残すのは、基準線、各案の最終モデル (screen と confirm)、Experiment で参照するもの。途中のスナップショットは残さない。
- `scripts/publish.py Exxxx` が、設定の `[run] publish` に書いたファイルを添付し、場所と sha256 を `experiments/Exxxx-*/artifacts.toml` に書く。
- `scripts/fetch.py Exxxx <案> [--seed N]` で、どのマシンからでも `runs/` に取り出せる (sha256 を確かめる)。

## 5. 環境と決定性

- パッケージ管理は uv。Python は `.python-version` の版。PyTorch の版を上げるときは `infra` の施策にする。
- 計算デバイスは cuda → mps → cpu の順に、使えるものを自動で選べる (`[run] device = "auto"`)。
- seed は引数で受け取り、`set_seed(seed, deterministic=True)` で決定的な実装を頼む。決定的な実装のない演算は警告が出る。
  同じ seed で結果が揺れるなら、その演算と対処を `.okf/architecture/machines.md` か Decision に書く。
- 学習のプロセスは、起動した時点のコードを最後まで使う。実行中に pull しても、その実行には反映されない。
