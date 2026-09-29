# <Team name> – 2026 BEHAVIOR Challenge submission

<!-- Shipped as README.md inside the submission zip. Fill in before packaging. -->

## Evaluation setup

- BEHAVIOR-1K tag: `v3.9.3-post1`
- Wrapper: `wrapper/rgbd_full_res_wrapper.py` (`omnigibson.eval.wrappers.RGBDFullResWrapper`, unchanged)
- Robot config: `robot_config/r1pro.yaml` (bundled `omnigibson/eval/r1pro.yaml`, unchanged)

## Evaluator command

```bash
python -m omnigibson.eval.eval \
    --task-name <task> \
    --host <host> --port <port> \
    --instance-indices <i> --num-envs 1 --num-rollouts 1 \
    --env-wrapper omnigibson.eval.wrappers.RGBDFullResWrapper \
    --robot-config robot_config/r1pro.yaml \
    --output-dir <out> --write-video
```

## Policy serving

<!-- Docker image name/tag and run command (must fit on one 24 GB GPU), or IP address + >= 50 ports. -->

## Rollout videos

<!-- Link to the uploaded videos (also submitted through the portal). -->
