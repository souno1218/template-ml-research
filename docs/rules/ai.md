# AI の作業規則

## 始めるとき

1. `CLAUDE.md` に書かれた順にルールを読み、最初の返答の 1 行目で「ルール v<VERSION> を読んだ。対象: …」と報告する。
2. `.okf/status.md` で、進行中の施策と実行中の計算を確かめる (SessionStart の hook も表示する)。
3. 対象の施策が決まっていなければ、人間に確かめる。新しい施策なら提案から始める (`lifecycle.md`)。

## 作業の単位

- **1 チャット = 1 施策。** 別の施策の話が出たら、その場で新しい施策の提案として切り出す (Proposal を書いて PR を作るところまで)。
- 施策の外の小さな変更 (ルールの誤字、スクリプトの不具合) は `kind: infra` の施策にする。ルールの中身を変えるときは `docs/rules/VERSION` を 1 つ上げる。

## 書く場所

| 何 | どこへ | いつ |
|---|---|---|
| 施策の提案と状態 | `.okf/proposals/Exxxx-*.md` | 提案するとき。状態が変わるたび |
| 結果の数字 | `experiments/Exxxx-*/results/` (`scripts/collect.py`) | 計算が終わったら |
| 結果の解釈と判定の案 | `.okf/experiments/Exxxx-*.md` | 結果を見たら |
| 採用・不採用の判定、方針・設計の決定 | `.okf/decisions/` | 決まったその場で |
| 研究の問い | `.okf/questions/Qn-*.md` | 問いを足す・変えるとき (Decision も書く) |
| 進行中・実行中の状況 | `.okf/status.md` | 状況が変わったら |
| 採用した仕組みの設計、マシンの記録 | `.okf/architecture/` | 採用の判定のとき。マシンで何か起きたとき |
| 外部の論文・資料 | `.okf/references/` | 参照したとき |

チャットで決めたことや分かったことを、チャットの中だけに残さない。次のチャットは、リポジトリしか読めない。
変更したら `.okf/log.md` に日付つきで 1 行足し、`uv run scripts/index.py` で索引を作り直す。

## Decision の扱い

- `status: stable` の Decision は守る。`draft` は提案中で、まだ縛らない。`deprecated` は置き換え済みの履歴 (`superseded_by` が後継)。
- 作業が stable の Decision とぶつかったら、黙って回避策を作らず、止まって人間に伝え、Decision の変更を提案する。
- 1 つの規則は 1 か所にだけ書き、ほかからはリンクする。Decision は今有効な内容だけを書き、修正の経緯は git に任せる。

## 書き方

- 文書とコメントは日本語。
- 確かめていないことには印を付ける: **[確認]** (コード・数字・記録で確かめた)、**[推定]** (読み取れるが確かめていない)、**[不明]**。
- 数式は `$$` を独立行に置いたディスプレイブロックで書き、すぐ下に torch 上の shape を batch 込みで書く (例: `(batch, <=block_size, n_embd)`)。
- 線形変換は $\left( N, D_{in} \right) \times \left( D_{in}, D_{out} \right) = \left( N, D_{out} \right)$ の向きで書く (`nn.Linear` の weight が (D_out, D_in) であることに対応)。
- Architecture には現在の形だけを書き、以前との差分や経緯は書かない。経緯は Experiment と Decision にある。
- 却下した案や試していないことは、commit メッセージにも残してよい: 本文の末尾に `Rejected: <案> (<理由>)`、`Not-tested: <何>` の行を書く。

## してはいけないこと

- 施策の中で `bench/` や `docs/rules/` を変える (hooks が止める)。
- 過去の数字を、今の施策の基準線として流用する (基準線は同じコード・同じ段階で測り直す)。
- 判定前のコードを `src/project_name/` に入れる。
- push していないコードで計算を回す、回してもらう (`scripts/run.py` が止める)。
- main に直接 push する。force push、`git reset --hard`、`--no-verify` を使う (hooks が止める)。
- `verified` を推測で付ける。人間が自分の id を明示したときだけ書く。

## 人間に頼むこと

- 施策の開始の承認 (Proposal の PR に「承認」とコメントしてもらう)。
- 採用の判定 (PR を main にマージしてもらう)。
- 手元の GPU マシンでの計算。`running.md` の形で、貼り付ければ動くコマンドを渡す。

## ルールを削る

ルールの版を上げるとき、またはモデルが変わったときに、各ルールが今も要るかを見直す。
hooks・テスト・スクリプトで機械的に守らせられるようになったルールは、文章から消してそちらに任せる。
