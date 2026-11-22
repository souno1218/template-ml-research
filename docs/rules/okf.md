# 知識ドキュメント (OKF) の書き方

知識ドキュメントは `.okf/` の Open Knowledge Format (OKF) v0.3 バンドルに置く。検討や実装を始める前に、
`.okf/index.md` と関係する種別の `index.md`、関係する Decision を読む。

## type

| type | 置き場所 | 内容 |
|---|---|---|
| Proposal | `.okf/proposals/` | 施策の提案と状態。人間が承認する |
| Experiment | `.okf/experiments/` | 実験の結果・予測との比較・考察・判定の案 |
| Decision | `.okf/decisions/` | 採用・不採用などの判断と理由 |
| Question | `.okf/questions/` | 研究の問い。施策は 1 つの問いに答えるために立てる |
| Status | `.okf/status.md` | 今どこにいるか (段階、基準線、進行中、実行中、次の候補) |
| Architecture | `.okf/architecture/` | 構成・設計・モデル構造・評価の設計・マシンの記録 |
| Reference | `.okf/references/` | 外部資料・論文・仕様の参照メモ |

これ以外の type を使うときは、理由を Decision に残す。雛形は `tools/okf/templates/`、施策の雛形は `experiments/_template/`。

## 書き方

- 1 ファイル 1 コンセプト。frontmatter に非空の `type` を必ず書く。
- `generated: { by: "claude/<model>", at: "<UTC の日時>" }` を自分の名義で書く。意味が変わらない整形では更新しない。
- 出典のない事実は書かない。`sources` に出典を書き、主張には脚注 (ラベルは `sources[].id`) を付ける。
  実験の数字の出典は `experiments/Exxxx-*/results/summary.md` (バンドルの外なので、ファイルからの相対パスで書く)。
- `verified` は、人間が確認して自分の id (`human:<id>`) を明示したときだけ追記する。推測で付けない。
- 既存ファイルを更新するときは、他者が書いたキー・`verified` 履歴・本文を保つ。
- バンドルの中を指すパス系フィールド (`resource` など) は先頭 `/` で書く。本文のリンクはファイルからの相対パスで書く。
- 置き換えた Decision は `status: deprecated` にし、`superseded_by` に後継を書く。
- 各ディレクトリの `index.md` は `uv run scripts/index.py` が作る (手で編集しない)。`.okf/index.md` と `.okf/log.md` は手で書く。
- 変更したら `.okf/log.md` (日付の新しい順) に 1 行足す。
- 終わる前に `uv run python tools/okf/validate.py .okf --strict` を実行し、エラーと警告を直す。

## 人間の承認

- Proposal は人間の承認を得てから実行に移す。判定は Decision に書き、PR のマージで確定する。
- 勝手に既存ドキュメントを書き換えない。書き直しは提案して承認を得てから行う。
