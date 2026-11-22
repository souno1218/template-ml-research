# 知識ドキュメント (OKF) の書き方

知識ドキュメントは `.okf/` の Open Knowledge Format (OKF) v0.3 バンドルに置く。仕様: https://github.com/open-knowledge-format/open-knowledge-format/blob/main/SPEC.md

検討や実装を始める前に、`.okf/index.md` と関係する種別の `index.md`、関係する Decision を読む。

## type の標準 (これ以外を使うときは理由を Decision に残す)

| type | 置き場所 | 内容 |
|---|---|---|
| Proposal | `.okf/proposals/Exxxx-*.md` | 施策の開始前に人間が承認する提案書 |
| Decision | `.okf/decisions/NNNN-*.md` | 採用・不採用・方針の判断と理由 |
| Experiment | `.okf/experiments/Exxxx-*.md` | 実験の設定・結果・考察・判定の案 |
| Architecture | `.okf/architecture/` | 構成・設計・モデル構造の説明 |
| Reference | `.okf/references/` | 外部資料・論文・仕様の参照メモ |

コードや結果のファイルは `experiments/Exxxx-*/` に置き、`.okf/` には入れない。Experiment の `resource` で `/experiments/Exxxx-*/` を指す。

## 書き方

- 1 ファイル 1 コンセプト。frontmatter に非空の `type` を必ず書く。雛形は `tools/okf/templates/`。
- `generated: { by: "claude/<model>", at: "<UTC の日時>" }` を自分の名義で書く。意味が変わらない整形では更新しない。
- 出典のない事実は書かない。`sources` に出典を書き、主張には脚注 (ラベルは `sources[].id`) を付ける。
- `verified` は、人間が確認して自分の id (`human:<id>`) を明示したときだけ追記する。推測で付けない。
- 既存ファイルを更新するときは、他者が書いたキー・`verified` 履歴・本文を保つ。
- パス系フィールド (`resource` など) は先頭 `/` で書く。本文のリンクはファイルからの相対パスで書く。
- このリポジトリ独自のキーは `x-` で始める (OKF の拡張キーの規則)。
- 変更したら、そのディレクトリの `index.md` と `.okf/log.md` (日付の新しい順) を更新する。
- 終わる前に `uv run python tools/okf/validate.py .okf --strict` を実行し、エラーと警告を直す。

## 人間の承認

- Proposal は人間の承認を得てから実行に移す。
- 勝手に既存ドキュメントを書き換えない。書き直しは提案して承認を得てから行う。
