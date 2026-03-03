"""
run_campaign.py — Single entry point for PyXIL-BMS test campaign.

Usage:
    python run_campaign.py

This script must be run from the repository root.
"""

import logging
import os
import sys

# ---------------------------------------------------------------------------
# Ensure the repository root is on the Python path.
# ---------------------------------------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

# ---------------------------------------------------------------------------
# Logging configuration — INFO to console, DEBUG to file
# ---------------------------------------------------------------------------
os.makedirs(os.path.join(_HERE, "reports"), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            os.path.join(_HERE, "reports", "campaign.log"), mode="w"
        ),
    ],
)

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
from framework.sequencer import Sequencer  # noqa: E402
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PyMIL-BMS Test Runner")
    parser.add_argument("--config", default="config/campaign.yaml", help="Path to campaign.yaml")
    parser.add_argument("--group", help="Filter tests by group (e.g., regression)")
    args = parser.parse_args()

    config_path = os.path.join(_HERE, args.config)
    sequencer = Sequencer(config_path=config_path)
    results = sequencer.run(group_filter=args.group)

    # Return exit code based on overall campaign verdict
    has_fail = any(r["verdict"] == "FAIL" for r in results.values())
    sys.exit(1 if has_fail else 0)
