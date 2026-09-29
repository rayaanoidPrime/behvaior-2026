"""Round-trips the evaluator's wire protocol against our server (no simulator needed)."""

import threading
import time
import urllib.request

import numpy as np
import pytest
import websockets.sync.client

from policy.policies import ZeroPolicy
from policy.protocol import ACTION_CHUNK_REQUEST_KEY, Packer, PolicyServer, unpackb

PORT = 18765


@pytest.fixture(scope="module")
def server():
    srv = PolicyServer(ZeroPolicy(), host="127.0.0.1", port=PORT, metadata={"policy": "zero"})
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    for _ in range(50):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/healthz", timeout=1) as r:
                if r.status == 200:
                    return srv
        except OSError:
            time.sleep(0.1)
    pytest.fail("server did not become healthy")


def _connect():
    return websockets.sync.client.connect(f"ws://127.0.0.1:{PORT}", compression=None, max_size=None)


def test_single_action(server):
    packer = Packer()
    obs = {"robot_r1::proprio": np.random.rand(61).astype(np.float32), "need_new_action": True}
    with _connect() as conn:
        assert unpackb(conn.recv()) == {"policy": "zero"}
        conn.send(packer.pack({"reset": True}))
        conn.send(packer.pack(obs))
        resp = unpackb(conn.recv())
    assert resp["action"].shape == (23,)
    assert resp["action"].dtype == np.float32
    assert "action_chunk" not in resp


def test_action_chunk(server):
    packer = Packer()
    obs = {"x": np.zeros(3, dtype=np.float32), ACTION_CHUNK_REQUEST_KEY: 8}
    with _connect() as conn:
        assert unpackb(conn.recv()) == {"policy": "zero"}
        conn.send(packer.pack(obs))
        resp = unpackb(conn.recv())
    assert resp["action_chunk"].shape == (8, 23)
    np.testing.assert_array_equal(resp["action_chunk"][0], resp["action"])
