"""
framework/sequencer.py — Layer 1

Responsibility:
    Campaign execution engine. Reads campaign.yaml, resolves test-case
    dependency ordering, dynamically imports and runs each test module,
    applies BLOCKED logic when a prerequisite fails, and delegates HTML
    report generation to reporter.py.
"""

import importlib
import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from .measurement import Measurement
from .reporter import Reporter
from .stimulator import Stimulator
from .verdict_engine import VerdictEngine

logger = logging.getLogger(__name__)

_VERDICT_RANK: Dict[str, int] = {
    "FAIL": 0,
    "INCONCLUSIVE": 1,
    "PASS": 2,
    "BLOCKED": -1,
}

_VERDICT_COLOR = {
    "PASS": "\033[92m",       # green
    "FAIL": "\033[91m",       # red
    "INCONCLUSIVE": "\033[93m",  # yellow
    "BLOCKED": "\033[90m",    # grey
}
_RESET = "\033[0m"


class Sequencer:
    """
    Campaign execution engine.

    Lifecycle:
        1. Load config/campaign.yaml.
        2. For each test (in priority order):
           a. Check depends_on — if parent FAILED, mark BLOCKED.
           b. Instantiate fresh Stimulator, Measurement, VerdictEngine.
           c. Dynamically import the test module and call run().
           d. Record result and duration.
        3. Print summary table to stdout.
        4. Delegate HTML report generation to Reporter.
    """

    def __init__(self, config_path: str = "config/campaign.yaml") -> None:
        self._config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self._results: Dict[str, Dict[str, Any]] = {}
        logger.debug("Sequencer initialised with config: %s", self._config_path)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, group_filter: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """
        Execute the test campaign and return results dict.
        
        Args:
            group_filter: Optional string to filter tests by 'group' field in campaign.yaml.

        Returns:
            {test_id: {name, verdict, duration_ms, details, signals_in,
                        signals_out}}
        """
        self._load_config()
        tests = self._config.get("tests", [])
        campaign_name = self._config.get("campaign_name", "Unnamed Campaign")

        # Sort by priority (ascending), then by position in file.
        tests_sorted = sorted(
            enumerate(tests), key=lambda x: (x[1].get("priority", 99), x[0])
        )

        # ----------------------------------------------------------
        # Dynamic MUT loading (Framework remains agnostic)
        # ----------------------------------------------------------
        model_path = self._config.get("model_class")
        model_cls = None
        if model_path:
            try:
                mod_name, cls_name = model_path.rsplit(".", 1)
                model_cls = getattr(importlib.import_module(mod_name), cls_name)
                logger.info("MUT Class Loaded: %s", model_path)
            except Exception as exc:
                logger.error("Failed to load model_class %s: %s", model_path, exc)

        logger.info("=" * 60)
        logger.info("CAMPAIGN: %s", campaign_name)
        logger.info("=" * 60)

        campaign_start = time.time()

        for _idx, test_cfg in tests_sorted:
            test_id: str = test_cfg["id"]
            test_name: str = test_cfg.get("name", test_id)
            module_path: str = test_cfg["module"]
            depends_on: Optional[str] = test_cfg.get("depends_on")
            test_group: Optional[str] = test_cfg.get("group")

            # ----------------------------------------------------------
            # Group filter
            # ----------------------------------------------------------
            if group_filter and test_group != group_filter:
                logger.debug("Skipping %s (group %s != %s)", test_id, test_group, group_filter)
                continue

            # ----------------------------------------------------------
            # Dependency check
            # ----------------------------------------------------------
            if depends_on:
                # Support single string or list of strings
                dep_list = [depends_on] if isinstance(depends_on, str) else depends_on
                
                for dep_id in dep_list:
                    parent = self._results.get(dep_id, {})
                    parent_verdict = parent.get("verdict", "UNKNOWN")
                    if parent_verdict in ("FAIL", "BLOCKED", "UNKNOWN"):
                        logger.warning(
                            "BLOCKED %s — parent %s verdict is %s.",
                            test_id,
                            dep_id,
                            parent_verdict,
                        )
                        self._results[test_id] = {
                            "name": test_name,
                            "verdict": "BLOCKED",
                            "duration_ms": 0,
                            "details": f"Blocked because {dep_id} = {parent_verdict}",
                            "signals_in": [],
                            "signals_out": [],
                            "verdict_history": [],
                        }
                        break
                
                if self._results.get(test_id, {}).get("verdict") == "BLOCKED":
                    continue

            # ----------------------------------------------------------
            # Fresh framework instances per test case (isolation)
            # ----------------------------------------------------------
            stimulator = Stimulator()
            measurement = Measurement()
            verdict_engine = VerdictEngine()

            # Inject model if configured
            if model_cls:
                # Fresh model instance per test case for isolation
                stimulator.model = model_cls()
            else:
                stimulator.model = None

            # ----------------------------------------------------------
            # Dynamic import and execution
            # ----------------------------------------------------------
            logger.info(">>> RUNNING %s: %s", test_id, test_name)
            start_ts = time.time()

            try:
                module = importlib.import_module(module_path)
                result: Dict[str, Any] = module.run(
                    stimulator, measurement, verdict_engine
                )
            except Exception as exc:  # pylint: disable=broad-except
                logger.exception("Exception in %s: %s", test_id, exc)
                result = {
                    "verdict": "FAIL",
                    "details": f"Exception: {exc}",
                    "signals_in": [],
                    "signals_out": [],
                }

            duration_ms = (time.time() - start_ts) * 1000

            self._results[test_id] = {
                "name": test_name,
                "verdict": result.get("verdict", "FAIL"),
                "duration_ms": round(duration_ms, 1),
                "details": result.get("details", ""),
                "signals_in": result.get("signals_in", []),
                "signals_out": result.get("signals_out", []),
                "verdict_history": verdict_engine.get_history(),
                "measurement": measurement,
            }

            logger.info(
                "<<< %s DONE in %.1f ms  verdict=%s",
                test_id,
                duration_ms,
                result.get("verdict"),
            )

        campaign_duration_s = time.time() - campaign_start
        self._print_summary(campaign_name, campaign_duration_s)
        Reporter().generate(campaign_name, self._results, campaign_duration_s)
        return self._results

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_config(self) -> None:
        with open(self._config_path, "r", encoding="utf-8") as fh:
            self._config = yaml.safe_load(fh)
        logger.debug("Campaign config loaded: %s", self._config)

    def _print_summary(
        self, campaign_name: str, duration_s: float
    ) -> None:
        total = len(self._results)
        pass_count = sum(
            1 for r in self._results.values() if r["verdict"] == "PASS"
        )
        pass_rate = (pass_count / total * 100) if total else 0.0

        print()
        print("=" * 72)
        print(f"  CAMPAIGN SUMMARY — {campaign_name}")
        print(f"  Duration: {duration_s:.2f}s   Pass rate: {pass_rate:.0f}%  ({pass_count}/{total})")
        print("=" * 72)
        print(
            f"  {'ID':<12} {'Name':<30} {'Verdict':<14} {'Duration (ms)'}"
        )
        print("-" * 72)
        for test_id, res in self._results.items():
            verdict = res["verdict"]
            color = _VERDICT_COLOR.get(verdict, "")
            print(
                f"  {test_id:<12} {res['name']:<30} "
                f"{color}{verdict:<14}{_RESET} {res['duration_ms']:.1f}"
            )
        print("=" * 72)
        print()
