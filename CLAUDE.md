# プロジェクトの規約

## 開発環境

- Python は uv で管理する（`uv sync`）。lint と整形は ruff、型検査は ty、テストは pytest。
- コミット前（pre-commit）と CI で、`uv run ruff check .` / `uv run ruff format --check .` / `uv run ty check` / `uv run pytest` / OKF の検証を実行する。変更を終える前に自分でも実行して通すこと。
- 最初に `pyproject.toml` の `name`、`src/project_name/` の名前、README の題を、プロジェクト名に合わせて直す。

## 機械学習・研究の運用

### 構成

- `src/project_name/` — モデル・学習などのライブラリ。`utils.py` にデバイス選択（cuda → mps → cpu）と seed 固定、`runinfo.py` に実行情報の収集がある。
- `src/project_name/eval/` — 評価コード。施策のコードから分けて置く。
- `scripts/` — 実行の入口。`configs/` — 設定。`outputs/` — 出力（git 管理しない）。
- 重みなどの成果物は git に入れず、GitHub Releases に置く。

### 施策の進め方

- 1つの施策は、1つの Proposal、1つのブランチ、1つの Experiment に対応させる。
- 人間の承認は「施策の開始（Proposal）」と「採用の判定（Decision）」の2か所だけ。その間の実装・実験は進めてよい。
- Experiment には、`collect_run_info()` の出力（コミット、dirty の有無、seed、デバイス、ホスト、torch のバージョン、日時）と設定を必ず書く。dirty が true の結果は採用の根拠にしない。
- 評価の方法を変えるときは、先に Decision を書く。過去の結果と比べられなくなる場合はそれを明記する。
- 採用しなかった施策のブランチも、Experiment と Decision に理由を残してから閉じる（マージしない施策を放置しない）。

### 実行

- 実行は、GitHub のブランチ上で動く状態にしてから行う。Mac と WSL のどちらでも同じコミットで動くこと。
- 重い計算は GPU のあるマシンで回す。Mac では1本ずつ回す。長時間の実行は tmux で動かし、GitHub から pull するところからコピペで動くコマンドを用意する。

### 引き継ぎ

- チャットやセッションをまたぐときは、現在地を Experiment と `.okf/log.md` に書く。次の担当は、リポジトリを読むだけで続きから始められるようにする。

### 数式と shape

- 数式は `$$` を独立行に置いたディスプレイブロックで書く。線形変換は PyTorch に合わせ $\left( N, D_{in} \right) \times \left( D_{in}, D_{out} \right) = \left( N, D_{out} \right)$ の向きで書く。
- 数式の下に torch 上の shape を、batch を含めて併記する（例: `(batch, <=block_size, n_embd)`）。

## 知識ドキュメントは OKF で書く

このプロジェクトの知識ドキュメントは `.okf/` の Open Knowledge Format (OKF) v0.3 バンドルに置く。検討や実装を始める前に、必ず次を読むこと。

1. `.okf/index.md` と、関係する種別の `index.md`
2. 関係する Decision（過去の判断と理由）

### type の標準（これ以外を使うときは理由を Decision に残す）

| type | 置き場所 | 内容 |
|---|---|---|
| Proposal | `.okf/proposals/` | 施策の開始前に人間が承認する提案書 |
| Decision | `.okf/decisions/` | 採用・不採用などの判断と理由 |
| Experiment | `.okf/experiments/` | 実験の設定・結果・考察 |
| Architecture | `.okf/architecture/` | 構成・設計・モデル構造の説明 |
| Reference | `.okf/references/` | 外部資料・論文・仕様の参照メモ |

### 書き方

- 1ファイル1コンセプト。frontmatter に非空の `type` を必ず書く。雛形は `tools/okf/templates/` にある。
- `generated: { by: "claude/<model>", at: "<UTC の日時>" }` を自分の名義で書く。意味が変わらない整形では更新しない。
- 出典のない事実は書かない。`sources` に出典を書き、主張には脚注（ラベルは `sources[].id`）を付ける。
- `verified` は、人間が確認して自分の id（`human:<id>`）を明示したときだけ追記する。推測で付けない。
- 既存ファイルを更新するときは、他者が書いたキー・`verified` 履歴・本文を保つ。
- パス系フィールド（`resource` など）は先頭 `/` で書く。本文のリンクはファイルからの相対パスで書く。
- 変更したら、そのディレクトリの `index.md` と `.okf/log.md`（日付の新しい順）を更新する。
- 終わる前に `python3 tools/okf/validate.py .okf --strict` を実行し、エラーと警告を直す。

### 人間の承認

- Proposal は人間の承認を得てから実行に移す。承認後に Decision を書く。
- 勝手に既存ドキュメントを書き換えない。書き直しは提案して承認を得てから行う。
