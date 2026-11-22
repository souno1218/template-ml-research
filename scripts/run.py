"""計算を回す: push 済みの commit からだけ実行し、実行の記録を残す。

    uv run scripts/run.py E0007 baseline --seed 0 -- uv run python scripts/train.py

--dev を付けると、commit と push の確認を省き、runs/dev/ に書く (collect.py は集計しない)。
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from project_name.runinfo import collect_run_info


def repo_root() -> Path:
    out = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True
    )
    return Path(out.stdout.strip())


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=False)


def check_pushed(root: Path) -> str | None:
    """実行してよい状態なら None、だめなら理由を返す。"""
    if _git(root, "status", "--porcelain").stdout.strip():
        return "作業ツリーに未コミットの変更がある。commit してから実行すること。"
    upstream = _git(root, "rev-parse", "@{u}")
    if upstream.returncode != 0:
        return "追跡している origin のブランチがない。`git push -u origin <ブランチ>` すること。"
    head = _git(root, "rev-parse", "HEAD").stdout.strip()
    if head != upstream.stdout.strip():
        return "HEAD が origin のブランチと一致しない。push または pull すること。"
    return None


def find_experiment_dir(root: Path, exp_id: str) -> Path:
    matches = sorted((root / "experiments").glob(f"{exp_id}-*"))
    if not matches:
        raise SystemExit(f"施策 {exp_id} のディレクトリが experiments/ にない。")
    return matches[0]


def run(root: Path, exp_id: str, variant: str, seed: int, command: list[str], dev: bool) -> int:
    if not dev:
        reason = check_pushed(root)
        if reason:
            print(f"実行を拒否: {reason}", file=sys.stderr)
            return 2
    exp_dir = find_experiment_dir(root, exp_id)
    config = exp_dir / "configs" / f"{variant}.toml"
    if not config.exists():
        print(f"実行を拒否: {config.relative_to(root)} がない。", file=sys.stderr)
        return 2
    info = collect_run_info(seed, root)  # 実行前のコードの状態 (dirty など) を記録する
    started = datetime.now().astimezone()
    run_id = f"{started:%Y%m%d-%H%M}-{exp_id}-{variant}-s{seed}"
    run_dir = root / "runs" / ("dev" if dev else "") / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    shutil.copy(config, run_dir / "config.toml")
    env = {
        **os.environ,
        "RUN_DIR": str(run_dir),
        "CONFIG": str(run_dir / "config.toml"),
        "EXPERIMENT_ID": exp_id,
        "VARIANT": variant,
        "SEED": str(seed),
    }
    with (run_dir / "log.txt").open("w") as log:
        process = subprocess.Popen(
            command,
            cwd=root,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        assert process.stdout is not None
        for line in process.stdout:
            sys.stdout.write(line)
            log.write(line)
        exit_code = process.wait()
    meta = {
        **info,
        "run_id": run_id,
        "experiment": exp_id,
        "variant": variant,
        "dev": dev,
        "started": started.isoformat(timespec="seconds"),
        "ended": datetime.now().astimezone().isoformat(timespec="seconds"),
        "exit_code": exit_code,
        "command": command,
    }
    (run_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n")
    print(f"記録: {run_dir.relative_to(root)}")
    return exit_code


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("experiment", help="施策 ID (E0007 など)")
    parser.add_argument("variant", help="案の名前 (configs/<案>.toml)")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--dev", action="store_true", help="動作確認用 (runs/dev/ に書く)")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="-- の後に実行するコマンド")
    args = parser.parse_args(argv)
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("実行するコマンドを -- の後に書くこと")
    return run(repo_root(), args.experiment, args.variant, args.seed, command, args.dev)


if __name__ == "__main__":
    raise SystemExit(main())
