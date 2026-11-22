# コードの規約

## 構成

```
src/project_name/
  registry.py   差し込み口 (名前 → 実装)
  jobs.py       ジョブ (scripts/run.py が設定の [run] job で選ぶ)。example は仕組みの確認用
  eval/         評価コード。施策のコードから分けて置く
  lab/          研究の道具 (Proposal の検査と索引、実行の記録、git の確認、評価一式の照合、集計)
  utils.py      デバイス選択と seed 固定
scripts/        実行の入口 (run、sweep、launch、collect、publish、fetch、new_experiment、index、progress)
scripts/hooks/  Claude Code の hooks (.claude/settings.json から呼ぶ)
configs/        基準線などの共通の設定
bench/suites/   評価一式 (版ごと)
experiments/    施策ごとの設定・試作・集計 (_template はテンプレート)
```

## 差し込み口 (registry)

差し替えうる部品は、名前で登録して設定ファイルから選ぶ。

```python
from project_name.registry import register


@register("model", "mlp")
class MLP(nn.Module): ...
```

- 決まっている種類は `registry.KINDS`。種類を足すときは `infra` の施策にする。
- 施策の試作は `experiments/Exxxx-*/code/` に置き、同じ `register` で登録する。設定ファイルの `[run] plugins` にそのディレクトリを書くと、実行時に読み込まれる。**試作のために `src/project_name/` を書き換えない。**
- 本体の部品が、試作のための差し込み口を持っていないときは、先に差し込み口を足す `infra` の施策を立てる。

## ジョブ

`job(cfg: dict, run_dir: Path, seed: int) -> None`。`metrics.json` を必ず書く。評価をするジョブは `per_sample.jsonl` も書く。
長いジョブは `lab.progress.ProgressWriter` で進み具合を書く。

## 規約

- 変更のたびに `uv run ruff check .`、`uv run ruff format --check .`、`uv run ty check`、`uv run pytest` を通す (pre-commit と CI でも実行する)。
- 文書とコメントは日本語。
- テンソルを扱う関数の docstring には、引数と戻り値の shape を batch 込みで書く (例: `x: (batch, seq, d_model)`)。
- 新しい部品には、少なくとも「形が保たれる」「並べ替えに等変 (該当する場合)」「パディングが漏れない (該当する場合)」のテストを付ける。
- 乱数は seed を引数で受け取り、グローバルな状態に頼らない。
- 値が発散しうる計算 (exp など) は、発散した値を計算グラフに入れない (loss の重みが 0 でも勾配が NaN になる)。
