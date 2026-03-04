"""
run_campaign.py — Single entry point for PyXIL-BMS test campaign.
"""

import argparse
import os
import sys

# Ensure repository root is in path
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from framework.sequencer import Sequencer
from framework.shared.logger import logger

def main():
    parser = argparse.ArgumentParser(description="PyXIL-BMS MIL Campaign Runner")
    parser.add_argument("--config", default="config/campaign.yaml", help="Path to campaign.yaml")
    parser.add_argument("--group", help="Filter tests by group")
    args = parser.parse_args()

    config_path = os.path.abspath(args.config)
    if not os.path.exists(config_path):
        logger.error(f"Campaign config not found: {config_path}")
        sys.exit(1)

    sequencer = Sequencer(config_path=config_path)
    
    try:
        results = sequencer.run(group_filter=args.group)
    except Exception as e:
        logger.error(f"Campaign execution failed: {e}")
        sys.exit(1)

    # Exit with code 1 if any test failed
    has_fail = any(r.get("verdict") == "FAIL" for r in results.values())
    if has_fail:
        logger.info("CAMPAIGN_END", message="Campaign finished with FAILURES.")
        sys.exit(1)
    else:
        logger.info("CAMPAIGN_END", message="Campaign finished SUCCESSFULLY.")
        sys.exit(0)

if __name__ == "__main__":
    main()
