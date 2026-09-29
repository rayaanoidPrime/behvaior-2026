import marimo

__generated_with = "0.25.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import os
    import subprocess
    from pathlib import Path

    import marimo as mo

    return Path, mo, os, subprocess


@app.cell
def _(mo):
    mo.md(r"""
    # BEHAVIOR 2026 on molab

    Attach a GPU first (notebook specs button in the header). Each step has its own button so
    nothing heavy runs when the notebook opens. Long steps run in the background and write a log
    under `~/b1k/logs/`; the log viewer at the bottom refreshes automatically.

    molab only keeps files created through its file browser, so a new session starts with an
    empty `~/b1k` and the install has to run again.
    """)
    return


@app.cell
def _(mo):
    repo_url = mo.ui.text(
        value="https://github.com/<you>/behvaior-2026.git", label="This repo's git URL", full_width=True
    )
    hf_token = mo.ui.text(kind="password", label="HF token (only needed for gated models)", full_width=True)
    mo.vstack([repo_url, hf_token])
    return hf_token, repo_url


@app.cell
def _(Path, os, subprocess):
    HOME = Path.home()
    REPO = HOME / "behvaior-2026"
    LOGS = HOME / "b1k" / "logs"
    LOGS.mkdir(parents=True, exist_ok=True)

    def sh(cmd: str) -> str:
        """Run a short command and return its combined output."""
        p = subprocess.run(["bash", "-lc", cmd], capture_output=True, text=True, cwd=REPO if REPO.exists() else HOME)
        return p.stdout + p.stderr

    def bg(name: str, cmd: str, env: dict | None = None) -> Path:
        """Start a long command in the background, logging to LOGS/<name>.log."""
        log = LOGS / f"{name}.log"
        with open(log, "w") as f:
            subprocess.Popen(
                ["bash", "-lc", cmd], cwd=REPO, stdout=f, stderr=subprocess.STDOUT,
                env={**os.environ, **(env or {})}, start_new_session=True,
            )
        return log

    return LOGS, REPO, bg, sh


@app.cell
def _(mo):
    clone_btn = mo.ui.run_button(label="1. Clone / update repo")
    check_btn = mo.ui.run_button(label="2. Check environment")
    install_btn = mo.ui.run_button(label="3. Install BEHAVIOR-1K (background, ~1h)")
    smoke_btn = mo.ui.run_button(label="4. Simulator smoke test (background)")
    mo.hstack([clone_btn, check_btn, install_btn, smoke_btn], justify="start", wrap=True)
    return check_btn, clone_btn, install_btn, smoke_btn


@app.cell
def _(REPO, clone_btn, mo, repo_url, sh):
    mo.stop(not clone_btn.value)
    _cmd = f"git -C {REPO} pull --ff-only" if REPO.exists() else f"git clone {repo_url.value} {REPO}"
    mo.plain_text(sh(_cmd))
    return


@app.cell
def _(check_btn, mo, sh):
    mo.stop(not check_btn.value)
    mo.plain_text(sh("bash scripts/check_env.sh"))
    return


@app.cell
def _(bg, install_btn, mo):
    mo.stop(not install_btn.value)
    _log = bg("install", "bash scripts/install_behavior.sh")
    mo.md(f"Started install, logging to `{_log}`")
    return


@app.cell
def _(bg, mo, smoke_btn):
    mo.stop(not smoke_btn.value)
    _log = bg("smoke", "bash scripts/smoke_test.sh turning_on_radio")
    mo.md(f"Started smoke test, logging to `{_log}`")
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Demos and evaluation
    """)
    return


@app.cell
def _(mo):
    tasks = mo.ui.text(value="turning_on_radio", label="Task name(s), space separated", full_width=True)
    policy = mo.ui.dropdown(options=["zero"], value="zero", label="Policy")
    demos_btn = mo.ui.run_button(label="Download demos for task(s)")
    eval_btn = mo.ui.run_button(label="Run eval (instances 0-9)")
    mo.vstack([tasks, policy, mo.hstack([demos_btn, eval_btn], justify="start")])
    return demos_btn, eval_btn, policy, tasks


@app.cell
def _(bg, demos_btn, hf_token, mo, tasks):
    mo.stop(not demos_btn.value)
    _env = {"HF_TOKEN": hf_token.value} if hf_token.value else None
    _log = bg("demos", f"pip install -q -U 'huggingface_hub[cli]' && bash scripts/download_demos.sh {tasks.value}", _env)
    mo.md(f"Downloading, logging to `{_log}`")
    return


@app.cell
def _(bg, eval_btn, mo, policy, tasks):
    mo.stop(not eval_btn.value)
    _cmds = " && ".join(f"POLICY={policy.value} bash scripts/run_eval.sh {t}" for t in tasks.value.split())
    _log = bg("eval", _cmds)
    mo.md(f"Evaluating, logging to `{_log}`")
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Logs
    """)
    return


@app.cell
def _(mo):
    refresh = mo.ui.refresh(default_interval="5s")
    log_pick = mo.ui.dropdown(options=["install.log", "smoke.log", "demos.log", "eval.log"], label="Log")
    mo.hstack([log_pick, refresh], justify="start")
    return log_pick, refresh


@app.cell
def _(LOGS, log_pick, mo, refresh):
    refresh
    mo.stop(not log_pick.value or not (LOGS / log_pick.value).exists(), mo.md("_No log yet._"))
    _lines = (LOGS / log_pick.value).read_text(errors="replace").splitlines()
    mo.plain_text("\n".join(_lines[-60:]))
    return


@app.cell
def _(REPO, mo):
    import json

    _rows = []
    for _p in sorted((REPO / "outputs" / "eval").glob("*/json/*.json")):
        _r = json.loads(_p.read_text())
        _rows.append({"task": _r["task"], "instance": _r["instance_id"], "success": _r["success"],
                      "q_score": _r["q_score"]["final"], "steps": _r["steps"]})
    mo.ui.table(_rows, label="Eval results") if _rows else mo.md("_No eval results yet._")
    return


if __name__ == "__main__":
    app.run()
