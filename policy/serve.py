"""Serve a policy for the BEHAVIOR-1K evaluator.

    python -m policy.serve --policy zero --port 8000
"""

from __future__ import annotations

import argparse
import logging

from policy.policies import POLICIES
from policy.protocol import PolicyServer


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--policy", choices=sorted(POLICIES), default="zero")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    policy = POLICIES[args.policy]()
    PolicyServer(policy, host=args.host, port=args.port, metadata={"policy": args.policy}).serve_forever()


if __name__ == "__main__":
    main()
