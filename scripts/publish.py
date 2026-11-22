"""施策の学習済みモデルを GitHub Releases (タグ models/Exxxx) に保管し、artifacts.toml に記録する。

collect.py で results/ に写した run (= 各案・各 seed の最新) が対象。保管するファイルは、
その run の設定の [run] publish (既定 ["model.pt"]) に書いた名前。
評価だけの run (学習済みのモデルを読んで評価するジョブ) は、
metrics.json の "model" に評価したモデルのパス (リポジトリの根から) を書いておけば、
それを model.pt として保管する。

  uv run scripts/publish.py E0001            # gh が要る (gh auth login 済み)
  uv run scripts/publish.py E0001 --dry-run  # 何を上げるかだけ表示
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path
from typing import Any

import tomli_w

from project_name.lab import gitstate
from project_name.lab.proposals import exp_dir, find
from project_name.lab.suite import sha256

DEFAULT_PUBLISH = ["model.pt"]


def _evaluated_model(root: Path, metrics_path: Path) -> Path | None:
    """評価だけの run が評価したモデルのパス。metrics.json の "model" (リポジトリの根から)。"""
    if not metrics_path.exists():
        return None
    model = json.loads(metrics_path.read_text()).get("model")
    return root / model if model else None


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("experiment")
    ap.add_argument("--runs-dir", default="runs")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    root = gitstate.repo_root()
    exp = find(root, args.experiment)
    edir = exp_dir(root, exp)
    tag = f"models/{args.experiment}"
    items: list[dict[str, Any]] = []
    for meta_path in sorted((edir / "results").glob("*/s*/meta.json")):
        meta = json.loads(meta_path.read_text())
        with open(meta_path.parent / "config.toml", "rb") as f:
            names = tomllib.load(f).get("run", {}).get("publish", DEFAULT_PUBLISH)
        run_dir = root / args.runs_dir / meta["run_id"]
        for name in names:
            src = run_dir / name
            if name == "model.pt" and not src.exists():
                src = _evaluated_model(root, meta_path.parent / "metrics.json") or src
            if not src.exists():
                print(f"見つからない (飛ばす): {src.relative_to(root)}")
                continue
            asset = f"{meta['variant']}-s{meta['seed']}-{name}"
            items.append(
                {
                    "variant": meta["variant"],
                    "seed": int(meta["seed"]),
                    "run_id": meta["run_id"],
                    "file": name,
                    "asset": asset,
                    "tag": tag,
                    "sha256": sha256(src),
                    "_src": src,
                }
            )
    if not items:
        print("保管するモデルがない (collect.py を先に回したか、run がモデルを書いたかを確かめる)")
        return 0

    for it in items:
        print(
            f"{'(dry-run) ' if args.dry_run else ''}{tag} ← {it['asset']}  "
            f"({it['_src'].stat().st_size:,} B)"
        )
    if args.dry_run:
        return 0

    # リリースの有無は REST で確かめる (gh release view は GraphQL を使い、使えない環境がある)
    exists = (
        subprocess.run(
            ["gh", "api", f"repos/{{owner}}/{{repo}}/releases/tags/{tag}"],
            cwd=root,
            capture_output=True,
        ).returncode
        == 0
    )
    if not exists:
        branch = gitstate.state(root).branch
        notes = f"{exp.meta.get('title', '')} の学習済みモデル。artifacts.toml を参照。"
        r = subprocess.run(
            [
                "gh",
                "release",
                "create",
                tag,
                "--target",
                branch,
                "--title",
                f"{args.experiment} のモデル",
                "--notes",
                notes,
            ],
            cwd=root,
            capture_output=True,
            text=True,
        )
        if r.returncode != 0:
            print(f"リリース {tag} を作れなかった: {r.stderr.strip()}", file=sys.stderr)
            print(
                "gh が使えるマシン (gh auth login 済み) で実行する。"
                "Claude のクラウド環境からは作れないことがある",
                file=sys.stderr,
            )
            return 1
    with tempfile.TemporaryDirectory() as tmp:
        paths = []
        for it in items:
            dst = Path(tmp) / it["asset"]
            shutil.copy2(it["_src"], dst)
            paths.append(str(dst))
        subprocess.run(["gh", "release", "upload", tag, *paths, "--clobber"], cwd=root, check=True)

    path = edir / "artifacts.toml"
    old = tomllib.loads(path.read_text()).get("model", []) if path.exists() else []
    keep = {(m["variant"], m["seed"], m["file"]): m for m in old}
    for it in items:
        keep[(it["variant"], it["seed"], it["file"])] = {
            k: v for k, v in it.items() if not k.startswith("_")
        }
    with open(path, "wb") as f:
        tomli_w.dump(
            {"model": sorted(keep.values(), key=lambda m: (m["variant"], m["seed"], m["file"]))}, f
        )
    print(f"書いた: {path.relative_to(root)}  (commit して push する)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
