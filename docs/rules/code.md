# コードの規約

## 構成

```
src/project_name/
  registry.py   差し込み口 (種類 + 名前 → 実装)
  utils.py      デバイス選択と seed 固定
  runinfo.py    実行情報の収集
  eval/         評価
scripts/        施策の管理と実行の道具 (new_experiment / run / collect)
experiments/    施策ごとの作業ディレクトリ (code / configs / results)
bench/          評価一式 (版管理)
```

## 差し込み口 (registry)

差し替えうる部品は、名前で登録して設定ファイルから選ぶ。

```python
from project_name.registry import register


@register("encoder", "my_encoder")
class MyEncoder(nn.Module): ...
```

- 種類 (`encoder` など) は自由に決めてよい。種類を足すときは、Decision に理由を残す。
- 施策の試作は `experiments/Exxxx-*/code/` に置き、同じ `register` で登録する。実行時に `load_plugins` で読み込む。**試作のために `src/` を書き換えない。**
- 本体の部品が、試作のための差し込み口を持っていないときは、先に差し込み口を足す `infra` の施策を立てる。

## 規約

- 変更のたびに ruff・ty・pytest を通す。
- テンソルを扱う関数の docstring には、引数と戻り値の shape を batch 込みで書く (例: `x: (batch, n_col, n_data)`)。
- 新しい部品には、少なくとも「形が保たれる」テストを付ける。並べ替えへの等変性、パディングの漏れがある部品は、それも確かめる。
- 乱数は seed を引数で受け取り、グローバルな状態に頼らない。
- 値が発散しうる計算 (exp など) は、発散した値を計算グラフに入れない (loss の重みが 0 でも勾配が NaN になる)。
