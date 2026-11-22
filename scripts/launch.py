"""施策の sweep を裏で回し、終わったら集計して結果を push する (人間のマシンで、1 行で動かす)。

AI が渡すのは次の 1 行だけ (ブランチ・commit・施策 ID を埋めて渡す):

  cd ~/<repo> && git fetch -q origin && git switch -q exp/E0001-x && git pull -q --ff-only \
      && uv sync -q && uv run scripts/launch.py E0001 --commit abc1234

これを貼ると、commit を照合し、pueue (https://github.com/Nukesor/pueue) のタスクとして登録して、
すぐに戻る。
端末を閉じても計算は続く。タスクは sweep.py → collect.py → (--publish なら) publish.py
→ 結果の commit と push を順に行う。様子は `pueue status`、`pueue follow <id>`、
`uv run scripts/progress.py E0001 --watch 60` で見る。pueue がなければ入れ方を表示して止まる。

Mac では、タスクが動いている間だけ caffeinate でスリープを止める
(pueue・--detach・--foreground のどれでも)。
ふたを閉じると止まることがあるので、ふたは開けたままにする。
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shlex
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

from project_name.lab import gitstate
from project_name.lab.proposals import exp_dir, find


def run(cmd: list[str], root: Path) -> int:
    print("$ " + " ".join(cmd), flush=True)
    return subprocess.run(cmd, cwd=root, check=False).returncode


def write_status(path: Path, **fields: object) -> None:
    data = json.loads(path.read_text()) if path.exists() else {}
    data.update(fields, updated=dt.datetime.now().isoformat(timespec="seconds"))
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1))


def keep_awake(platform: str = sys.platform, which=shutil.which, popen=subprocess.Popen) -> bool:
    """Mac なら、このプロセスが終わるまでスリープを止める caffeinate を裏で起動する。

    起動したら True。

    -i (アイドルでのスリープ)、-m (ディスク)、-s (電源につないでいるときのシステムの
    スリープ) を止める。
    -w でこのプロセスの終了を待つので、計算が終われば caffeinate も終わる。
    """
    if platform != "darwin" or which("caffeinate") is None:
        return False
    popen(["caffeinate", "-ims", "-w", str(os.getpid())])
    return True


def child(args: argparse.Namespace, root: Path, status: Path) -> int:
    """裏で動く本体。各段階の結果を status に書き、失敗したらそこで止める (push しない)。"""
    if keep_awake():
        msg = "Mac: 計算が終わるまで caffeinate でスリープを止める (ふたは開けたままにする)"
        print(msg, flush=True)
    stem = exp_dir(root, find(root, args.experiment)).name
    sweep = Path(args.sweep) if args.sweep else root / "experiments" / stem / "sweep.toml"
    py, here = sys.executable, Path(__file__).resolve().parent
    steps: list[tuple[str, list[str]]] = [
        ("sweep", [py, str(here / "sweep.py"), str(sweep)]),
        ("collect", [py, str(here / "collect.py"), args.experiment]),
    ]
    if args.publish:
        steps.append(("publish", [py, str(here / "publish.py"), args.experiment]))
    for name, cmd in steps:
        write_status(status, phase=name, state="running")
        if run(cmd, root) != 0:
            write_status(status, phase=name, state="failed")
            print(f"失敗: {name}。ここで止めた (結果は push していない)", flush=True)
            return 1
    if args.no_push:
        write_status(status, phase="done", state="ok")
        return 0
    write_status(status, phase="push", state="running")
    message = f"{args.experiment}: {socket.gethostname()} の結果"
    for cmd in (
        ["git", "add", f"experiments/{stem}"],
        ["git", "commit", "-m", message],
        ["git", "push"],
    ):
        if run(cmd, root) != 0:
            write_status(status, phase="push", state="failed")
            print("push に失敗した。手で git push する", flush=True)
            return 1
    write_status(status, phase="done", state="ok")
    print("全部終わった。結果を push した", flush=True)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("experiment", help="施策の ID (E0001 など)")
    ap.add_argument("--commit", required=True, help="AI が指定した commit (短い形でよい)")
    ap.add_argument("--sweep", help="sweep.toml (省略すると experiments/<施策>/sweep.toml)")
    ap.add_argument(
        "--publish", action="store_true", help="終わったらモデルを GitHub Releases に保管する"
    )
    ap.add_argument("--no-push", action="store_true", help="結果を commit・push しない")
    ap.add_argument("--foreground", action="store_true", help="裏に回さず、この端末で動かす")
    ap.add_argument(
        "--detach", action="store_true", help="pueue を使わず、切り離したプロセスで回す"
    )
    ap.add_argument("--child", help=argparse.SUPPRESS)
    args = ap.parse_args()

    root = gitstate.repo_root()
    if args.child:
        return child(args, root, Path(args.child))

    st = gitstate.state(root)
    if not st.commit.startswith(args.commit):
        print(
            f"NG: commit が違う (今は {st.short}、指定は {args.commit})。ここで止めて AI に伝える"
        )
        return 2
    problems = gitstate.check_runnable(st)
    if problems:
        print("NG: 実行できない状態 (docs/rules/running.md):")
        for p in problems:
            print(f"  - {p}")
        return 2

    out = root / "runs" / "_launch"
    out.mkdir(parents=True, exist_ok=True)
    name = f"{dt.datetime.now():%Y%m%d-%H%M%S}-{args.experiment}"
    log, status = out / f"{name}.log", out / f"{name}.json"
    write_status(
        status, experiment=args.experiment, commit=st.commit, phase="start", state="running"
    )
    if args.foreground:
        return child(args, root, status)
    cmd = [sys.executable, str(Path(__file__).resolve()), args.experiment, "--commit", args.commit]
    cmd += ["--sweep", args.sweep] if args.sweep else []
    cmd += ["--publish"] if args.publish else []
    cmd += ["--no-push"] if args.no_push else []
    cmd += ["--child", str(status)]
    if args.detach:
        return start_detached(cmd, root, status, log, args.experiment, st.short)
    return start_pueue(cmd, root, status, args.experiment, st.short)


PUEUE_INSTALL = """pueue が見つからない。入れてから同じ 1 行をもう一度貼る:
  Mac:            brew install pueue
  Linux / WSL:    パッケージにあれば sudo apt install pueue、なければ cargo install --locked pueue
                  (または https://github.com/Nukesor/pueue/releases のバイナリを PATH に置く)
入れたら pueued -d でデーモンを起動する (このスクリプトも起動を試みる)。
pueue を使わずに裏で回すだけなら、末尾に --detach を付ける。"""


def pueue_ready() -> bool:
    """pueue があり、デーモン (pueued) が動いているか。止まっていれば起動を試みる。"""
    if shutil.which("pueue") is None:
        return False
    ok = subprocess.run(["pueue", "status"], capture_output=True, check=False).returncode == 0
    if not ok and shutil.which("pueued") is not None:
        subprocess.run(["pueued", "-d"], capture_output=True, check=False)
        time.sleep(1)
        ok = subprocess.run(["pueue", "status"], capture_output=True, check=False).returncode == 0
    return ok


def start_pueue(cmd: list[str], root: Path, status: Path, exp: str, short: str) -> int:
    """pueue のタスクとして登録する。ログと状態は pueue で見る (普通の端末の操作のまま)。"""
    if not pueue_ready():
        print(PUEUE_INSTALL)
        return 2
    add = ["pueue", "add", "--print-task-id", "--label", exp, "--working-directory", str(root)]
    r = subprocess.run([*add, "--", shlex.join(cmd)], capture_output=True, text=True, check=False)
    if r.returncode != 0:
        print(f"NG: pueue に登録できなかった: {r.stderr.strip()}")
        return 2
    task = r.stdout.strip()
    write_status(status, pueue_task=task)
    print(f"OK: commit {short} で {exp} を pueue に登録した (タスク {task})。端末は閉じてよい")
    print(f"  ログ:     pueue follow {task}   (Ctrl-C で見るのをやめても計算は続く)")
    print("  一覧:     pueue status")
    print(f"  進み具合: uv run scripts/progress.py {exp} --watch 60")
    print(
        f"  止める:   pueue kill {task}  (同じ 1 行をもう一度貼ると、終わっていない run から続ける)"
    )
    return 0


def start_detached(
    cmd: list[str], root: Path, status: Path, log: Path, exp: str, short: str
) -> int:
    """pueue のないマシン用: 端末から切り離したプロセスで回す。"""
    with open(log, "w") as fh:  # 子プロセスが複製を持つので、親側はすぐ閉じてよい
        # start_new_session: 端末から切り離す (端末を閉じても止まらない。Mac と Linux で効く)
        p = subprocess.Popen(
            cmd,
            cwd=root,
            stdout=fh,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )
    write_status(status, pid=p.pid, log=str(log.relative_to(root)))
    print(f"OK: commit {short} で {exp} を裏で始めた (pid {p.pid})。端末は閉じてよい")
    print(f"  ログ:     tail -f {log.relative_to(root)}")
    print(f"  進み具合: uv run scripts/progress.py {exp} --watch 60")
    print(
        f"  止める:   kill -- -{p.pid}  (同じ 1 行をもう一度貼ると、終わっていない run から続ける)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
