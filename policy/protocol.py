"""Standalone websocket policy server compatible with the BEHAVIOR-1K evaluator.

Wire format mirrors ``omnigibson/eval/utils/network_utils.py`` (BEHAVIOR-1K v3.9.3-post1),
which is itself adapted from openpi:

* The evaluator polls ``GET /healthz`` until it returns 200, then opens a websocket.
* On connect the server sends a msgpack-encoded metadata dict.
* Each request is a msgpack dict of flattened observations (numpy arrays encoded with the
  ``__ndarray__`` extension below). ``{"reset": True}`` signals an episode reset and gets no reply.
* Each reply is ``{"action": np.ndarray[..., action_dim]}``. If the request carries
  ``__action_chunk_size__ = K`` and the policy supports chunks, the reply also carries
  ``"action_chunk": np.ndarray[..., K, action_dim]`` whose first step equals ``action``.

This module deliberately depends only on numpy, msgpack and websockets so the policy can run in
its own environment (or Docker image) without OmniGibson / Isaac Sim installed.
"""

from __future__ import annotations

import asyncio
import functools
import http
import logging
import time
import traceback
from typing import Any, Protocol

import msgpack
import numpy as np
import websockets
import websockets.asyncio.server as _server

logger = logging.getLogger(__name__)

ACTION_CHUNK_REQUEST_KEY = "__action_chunk_size__"


class Policy(Protocol):
    def act(self, obs: dict[str, Any]) -> np.ndarray: ...

    def reset(self) -> None: ...


# --- msgpack numpy extension (same encoding as the evaluator) -------------------------------------


def pack_data(obj):
    if isinstance(obj, np.ndarray):
        if obj.dtype.kind in ("V", "O", "c"):
            raise ValueError(f"Unsupported dtype: {obj.dtype}")
        return {b"__ndarray__": True, b"data": obj.tobytes(), b"dtype": obj.dtype.str, b"shape": obj.shape}
    if isinstance(obj, np.generic):
        return {b"__npgeneric__": True, b"data": obj.item(), b"dtype": obj.dtype.str}
    return obj


def unpack_data(obj):
    if b"__ndarray__" in obj:
        return np.ndarray(buffer=obj[b"data"], dtype=np.dtype(obj[b"dtype"]), shape=obj[b"shape"])
    if b"__npgeneric__" in obj:
        return np.dtype(obj[b"dtype"]).type(obj[b"data"])
    return obj


Packer = functools.partial(msgpack.Packer, default=pack_data)
packb = functools.partial(msgpack.packb, default=pack_data)
unpackb = functools.partial(msgpack.unpackb, object_hook=unpack_data)


# --- server ---------------------------------------------------------------------------------------


def describe_obs(obs: dict[str, Any]) -> str:
    lines = []
    for k, v in sorted(obs.items()):
        if isinstance(v, np.ndarray):
            lines.append(f"  {k}: {v.dtype} {tuple(v.shape)}")
        else:
            lines.append(f"  {k}: {type(v).__name__} = {v!r}"[:200])
    return "\n".join(lines)


class PolicyServer:
    def __init__(self, policy: Policy, host: str = "0.0.0.0", port: int = 8000, metadata: dict | None = None):
        self._policy = policy
        self._host = host
        self._port = port
        self._metadata = metadata or {}
        self._logged_obs_schema = False

    def serve_forever(self) -> None:
        asyncio.run(self.run())

    async def run(self) -> None:
        logger.info("Serving policy on ws://%s:%d (health: /healthz)", self._host, self._port)
        async with _server.serve(
            self._handler,
            self._host,
            self._port,
            compression=None,
            max_size=None,
            process_request=_health_check,
        ) as server:
            await server.serve_forever()

    async def _handler(self, websocket) -> None:
        logger.info("Connection from %s opened", websocket.remote_address)
        packer = Packer()
        await websocket.send(packer.pack(self._metadata))

        while True:
            try:
                request = unpackb(await websocket.recv(), strict_map_key=False)
                if "reset" in request:
                    self._policy.reset()
                    continue

                chunk_size = int(request.pop(ACTION_CHUNK_REQUEST_KEY, 0) or 0)
                if not self._logged_obs_schema:
                    logger.info("First observation schema:\n%s", describe_obs(request))
                    self._logged_obs_schema = True

                t0 = time.monotonic()
                response: dict[str, Any] = {}
                if chunk_size > 1 and hasattr(self._policy, "act_chunk"):
                    chunk = np.asarray(self._policy.act_chunk(request, chunk_size), dtype=np.float32)
                    response["action"] = np.ascontiguousarray(chunk[..., 0, :])
                    response["action_chunk"] = chunk
                else:
                    response["action"] = np.asarray(self._policy.act(request), dtype=np.float32)
                response["server_timing"] = {"infer_ms": (time.monotonic() - t0) * 1000}

                await websocket.send(packer.pack(response))
            except websockets.ConnectionClosed:
                logger.info("Connection from %s closed", websocket.remote_address)
                break
            except Exception:
                tb = traceback.format_exc()
                logger.error("Error serving %s:\n%s", websocket.remote_address, tb)
                # A str frame is surfaced by the evaluator as "Error in inference server".
                await websocket.send(tb)
                await websocket.close(code=1011, reason="Internal server error")
                raise


def _health_check(connection, request):
    if request.path == "/healthz":
        return connection.respond(http.HTTPStatus.OK, "OK\n")
    return None
