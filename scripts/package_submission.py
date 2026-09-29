"""Scores eval outputs and builds the final submission zip.

    python scripts/package_submission.py --team my_team \
        [--wrapper path/to/wrapper.py] [--robot-config configs/r1pro.yaml]

Reads outputs/eval/<task>/json/*.json (written by scripts/run_eval.sh), reports the leaderboard
score (mean q_score over 100 tasks x 10 instances, missing rollouts count as 0), and writes
outputs/submission_<team>.zip with the metrics JSONs, wrapper, robot config and README.
Videos are not zipped: upload outputs/eval/*/videos somewhere and submit the link on the portal.
"""

from __future__ import annotations

import argparse
import json
import os
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
N_TASKS = 100
N_INSTANCES = 10


def load_results(eval_dir: Path) -> dict[str, list[dict]]:
    results: dict[str, list[dict]] = {}
    for path in sorted(eval_dir.glob("*/json/*.json")):
        with open(path) as f:
            r = json.load(f)
        r["_path"] = path
        results.setdefault(r["task"], []).append(r)
    return results


def main() -> None:
    b1k = Path(os.environ.get("PATH_TO_BEHAVIOR_1K", Path.home() / "b1k" / "BEHAVIOR-1K"))
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--team", required=True)
    parser.add_argument("--eval-dir", type=Path, default=REPO_ROOT / "outputs" / "eval")
    parser.add_argument(
        "--wrapper",
        type=Path,
        default=b1k / "OmniGibson" / "omnigibson" / "eval" / "wrappers" / "rgbd_full_res_wrapper.py",
    )
    parser.add_argument("--robot-config", type=Path, default=REPO_ROOT / "configs" / "r1pro.yaml")
    parser.add_argument("--readme", type=Path, default=REPO_ROOT / "SUBMISSION_README.md")
    args = parser.parse_args()

    results = load_results(args.eval_dir)
    total_q = 0.0
    print(f"{'task':50s} {'n':>3s} {'mean_q':>7s} {'succ':>5s}")
    for task, rs in sorted(results.items()):
        instances = {r["instance_id"]: r for r in rs if r.get("rollout_id", 0) == 0}
        q = [instances[i]["q_score"]["final"] if i in instances else 0.0 for i in range(N_INSTANCES)]
        total_q += sum(q)
        n_succ = sum(bool(r["success"]) for r in instances.values())
        print(f"{task:50s} {len(instances):3d} {sum(q) / N_INSTANCES:7.3f} {n_succ:5d}")
    print(f"\nTasks with results: {len(results)}/{N_TASKS}")
    print(f"Leaderboard score (missing = 0): {total_q / (N_TASKS * N_INSTANCES):.4f}")

    for p in (args.wrapper, args.robot_config, args.readme):
        if not p.is_file():
            raise SystemExit(f"missing required file: {p}")

    out = REPO_ROOT / "outputs" / f"submission_{args.team}.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for rs in results.values():
            for r in rs:
                zf.write(r["_path"], f"json/{r['_path'].name}")
        zf.write(args.wrapper, f"wrapper/{args.wrapper.name}")
        zf.write(args.robot_config, f"robot_config/{args.robot_config.name}")
        zf.write(args.readme, "README.md")
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
