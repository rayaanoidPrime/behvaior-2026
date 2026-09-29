"""Policies served to the BEHAVIOR evaluator. Replace / extend with your own model."""

from __future__ import annotations

from typing import Any

import numpy as np

# R1Pro action layout used by the 2026 demo dataset (meta/info.json: action float32[23]) and the
# default eval robot config (configs/r1pro.yaml). Verify against the evaluator before relying on it.
R1PRO_ACTION_DIM = 23


class ZeroPolicy:
    """Returns an all-zero action every step.

    Only useful for checking the plumbing (evaluator <-> server, videos, JSON output).
    With the default absolute joint-position controllers, zeros drive the arms to their
    reset pose and straighten the trunk; the base stays still.
    """

    def __init__(self, action_dim: int = R1PRO_ACTION_DIM):
        self.action_dim = action_dim

    def act(self, obs: dict[str, Any]) -> np.ndarray:
        return np.zeros(self.action_dim, dtype=np.float32)

    def act_chunk(self, obs: dict[str, Any], chunk_size: int) -> np.ndarray:
        return np.zeros((chunk_size, self.action_dim), dtype=np.float32)

    def reset(self) -> None:
        pass


POLICIES = {"zero": ZeroPolicy}
