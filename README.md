# BEHAVIOR Challenge 2026

Entry for the [2026 BEHAVIOR Challenge](https://behavior.stanford.edu/challenge/index.html):
100 long-horizon household tasks in OmniGibson (Isaac Sim), scored by BDDL partial-credit
`q_score` averaged over 100 tasks × 10 public test instances.

| | |
|---|---|
| Submission deadline | **2026-10-16** |
| Winners announced | 2026-11-04 |
| Track | RGB + depth + proprioception only (no privileged sim state at eval time) |
| Simulator | [BEHAVIOR-1K](https://github.com/StanfordVL/BEHAVIOR-1K) `v3.9.3-post1` (docs say `v3.9.3`; that tag was published as `-post1`) |
| Demos | [behavior-1k/2026-challenge-demos](https://huggingface.co/datasets/behavior-1k/2026-challenge-demos), LeRobot v3, 3.27 TB, 200 demos/task |
| Baselines | π0.5 ([openpi fork](https://github.com/wensi-ai/openpi/tree/behavior)), GR00T N1.7 ([Isaac-GR00T fork](https://github.com/wensi-ai/Isaac-GR00T)) |
| Submit | [portal](https://behavior-1k-2026-challenge-leaderboard.hf.space/submit) · [leaderboard](https://huggingface.co/spaces/behavior-1k/2026-challenge-leaderboard) · [Discord](https://discord.gg/bccR5vGFEx) |

## How evaluation works

Two processes talk over a websocket:

```
OmniGibson evaluator  --(msgpack obs)-->  policy server (this repo: policy/)
 python -m omnigibson.eval.eval  <--(action[23])--  python -m policy.serve
```

`policy/protocol.py` implements the server side of the evaluator's protocol with only
numpy/msgpack/websockets, so the policy can run in its own env or Docker image. Plug a model in
by adding a class with `act(obs) -> np.ndarray[23]` and `reset()` to `policy/policies.py`
(optionally `act_chunk(obs, k)` for open-loop action chunks). The server logs the observation
schema on the first request.

## Running on molab

This laptop has no GPU; the simulator runs on a [molab](https://molab.marimo.io) notebook with
the RTX Pro 6000 GPU attached.

1. The repo lives at https://github.com/rayaanoidPrime/behvaior-2026 (private); create a
   fine-grained GitHub token with read access to it for the notebook's clone step.
2. Open `notebooks/molab_setup.py` in molab, attach the GPU, paste the token.
3. Click through the buttons in order:
   1. **Clone** this repo into `~/behvaior-2026`.
   2. **Check environment** (`scripts/check_env.sh`): GPU, Vulkan/graphics driver libs, disk, RAM.
      Read this output before installing anything; see the caveats below.
   3. **Install** (`scripts/install_behavior.sh`): user-space Miniforge, BEHAVIOR-1K at the pinned
      tag, then upstream `setup.sh --omnigibson --bddl --eval --dataset`. This accepts the Conda
      ToS, NVIDIA Omniverse EULA and BEHAVIOR data license on your behalf.
   4. **Smoke test** (`scripts/smoke_test.sh`): one task, 50 zero-action steps, no server. If this
      writes a video to `outputs/smoke/`, rendering works.
4. **Eval** (`scripts/run_eval.sh <task>`): starts `policy.serve` and runs the official settings
   (`RGBDFullResWrapper`, instances 0–9, 1 rollout, videos on).

### molab caveats

- **Rendering support is unverified.** Isaac Sim needs the container to expose NVIDIA graphics
  (Vulkan) as well as compute. `check_env.sh` looks for this; if the smoke test fails with Vulkan
  or RTX errors, molab can't run the simulator and you need a VM with an RTX-class GPU (for
  example an L4, L40S or A10G; A100/H100 have no RT cores).
- **Nothing persists between sessions** unless it was created through the file browser. That
  means reinstalling (tens of GB) in every session. Push checkpoints and results somewhere
  durable (a HF bucket or repo) before a session ends. Sessions last at most 12 h and stop after
  90 min idle.
- **Resources:** 4 CPUs and 32 GB RAM by default. Keep `NUM_ENVS=1` until memory use is known.
  Scene loading takes about 2–5 min for each instance.
- **Final submission** needs either a Docker image that serves the policy (it must fit on one
  24 GB GPU) or a public IP address with 50 or more ports. molab provides neither, so build the
  image with GitHub Actions or on a Linux machine.

## Local (no GPU)

```bash
uv run --group dev pytest          # protocol round-trip tests
uv run python -m policy.serve      # zero policy on :8000
```

## Layout

```
policy/            websocket policy server + policies (the part you submit)
scripts/           env.sh (paths/tag), check_env, install_behavior, smoke_test,
                   download_demos, run_eval, package_submission.py
notebooks/         molab_setup.py – marimo driver for the scripts above
configs/           r1pro.yaml (eval robot config, copied from upstream), task_data.json (100 tasks)
SUBMISSION_README.md   template shipped inside the submission zip
outputs/           eval JSONs/videos (git-ignored)
```

## Submitting

```bash
python scripts/package_submission.py --team <name>
```

This prints the leaderboard-style score, with missing rollouts counted as 0, and zips the metrics
JSONs, the wrapper, the robot config and `SUBMISSION_README.md`. Upload the rollout videos separately and link them on
the portal. Rules: report one rollout per instance (no cherry-picking), don't edit the output
files, and include any custom wrapper or robot config you used.
