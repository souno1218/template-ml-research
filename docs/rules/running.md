# 実行の手順

## 1. GitHub を唯一の受け渡し口にする

コードも結果も、必ず GitHub のブランチを経由する。ファイルやバンドルの直接の受け渡しはしない。

- 学習・評価は `scripts/run.py` 経由で回す。
- `run.py` は次のときに実行を拒否する:
  - 作業ツリーに未コミットの変更がある
  - HEAD が、追跡している `origin` のブランチと一致しない (push していない、または pull していない)
- 例外は `--dev`。動作確認用で、`runs/dev/` に書かれ、`collect.py` は集計しない。

```bash
uv run scripts/run.py E0007 baseline --seed 0 -- uv run python scripts/train.py
```

実行するコマンドには、環境変数 `RUN_DIR`、`CONFIG`、`EXPERIMENT_ID`、`VARIANT`、`SEED` が渡される。

## 2. 実行の記録

`runs/<run_id>/` に次を残す (`run.py` が書く)。

| ファイル | 中身 |
|---|---|
| `config.toml` | `experiments/Exxxx-*/configs/<案>.toml` の写し |
| `meta.json` | run_id、施策、案、seed、commit、ブランチ、マシン名、デバイス、ライブラリの版、開始・終了の時刻、終了コード、コマンド |
| `log.txt` | 標準出力と標準エラー |
| `metrics.json` | 集計の指標 (ジョブが `RUN_DIR` に書く) |

run_id は `<日付時刻>-<施策ID>-<案>-s<seed>`。`runs/` は git の管理外。
結果は `scripts/collect.py Exxxx` で `experiments/Exxxx-*/results/` に写して commit する。

## 3. マシンごとの流れ

| マシン | 誰が回すか | 流れ |
|---|---|---|
| Mac など、Claude が直接動かせるマシン | Claude が直接 | ブランチに push → その commit のまま実行 → `collect.py` → 結果を commit・push |
| GPU のあるマシン (WSL など) | 人間が手で | AI がブランチに push し、下の形のコマンドを渡す → 人間が tmux に貼り付けて実行 → 結果を push → AI が pull して Experiment を書く |

- 同じ施策の中で比べる数字は、同じ種類のマシンで出したものに限る。
- 長い計算 (目安 1 時間以上) を始めたら、`docs/status.md` の「実行中」に、マシン・コマンド・開始時刻・終わる見込みを書く。
- マシンの構成・速さ・起きた問題は `docs/machines.md` に書く。計算を頼む前に読む。

### GPU マシンに渡すコマンドの形

AI は、ブランチ名・commit・施策 ID をすべて埋めた状態で渡す。人間は上から順に貼り付けるだけで動くこと。

```bash
# 1. tmux の中で動かす (接続が切れても続く。抜けるのは Ctrl-b d、戻るのは tmux attach -t E0007)
tmux new -s E0007

# 2. 指定の commit に合わせる
cd ~/<repo> && git fetch origin && git switch exp/E0007-slug && git pull --ff-only
test "$(git rev-parse --short HEAD)" = "abc1234" && echo "OK: commit 一致" || echo "NG: commit が違う。ここで止めて AI に伝える"
uv sync

# 3. 実行
uv run scripts/run.py E0007 baseline --seed 0 -- uv run python scripts/train.py

# 4. 終わったら: 集計・結果の push
uv run scripts/collect.py E0007
git add experiments/E0007-slug && git commit -m "E0007: <マシン名> の結果" && git push
```

初めてのマシンでは、先に `git clone` と `gh auth login` を済ませておく。

## 4. 学習済みモデルなどの成果物

- git には入れない (`.gitignore` 済み)。保管先は **GitHub Releases**。施策ごとに 1 つのリリース (タグ `models/Exxxx`) を作り、残すものを添付する。
- 場所と sha256 は `experiments/Exxxx-*/artifacts.toml` に書いて commit する。
- 残すのは、基準線、各案の最終モデル、Experiment で参照するもの。途中のスナップショットは残さない。

## 5. 環境

- パッケージ管理は uv。Python は `.python-version` の版。依存を上げるときは `infra` の施策にする。
- 計算デバイスは cuda → mps → cpu の順に自動で選ぶ (`project_name.utils.get_device`)。
- 学習のプロセスは、起動した時点のコードを最後まで使う。実行中に pull しても、その実行には反映されない。
