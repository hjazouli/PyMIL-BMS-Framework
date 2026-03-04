import importlib
import time
from pathlib import Path
from typing import Any, Dict, Optional
import yaml

from .base.base_sequencer import BaseSequencer
from .mil.mil_stimulator import MILStimulator
from .mil.mil_measurement import MILMeasurement
from .verdict_engine import VerdictEngine
from .reporter import Reporter
from .shared.logger import logger

_VERDICT_COLOR = {
    "PASS": "\033[92m",
    "FAIL": "\033[91m",
    "INCONCLUSIVE": "\033[93m",
    "BLOCKED": "\033[90m",
}
_RESET = "\033[0m"

class Sequencer(BaseSequencer):
    """
    Concrete implementation of the campaign execution engine.
    """

    def __init__(self, config_path: str = "config/campaign.yaml") -> None:
        self._config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self._results: Dict[str, Dict[str, Any]] = {}
        logger.info("CAMPAIGN_START", message=f"Sequencer initialized with config: {self._config_path}")

    def load_campaign(self, config_path: str) -> None:
        self._config_path = Path(config_path)
        with open(self._config_path, "r", encoding="utf-8") as fh:
            self._config = yaml.safe_load(fh)
        logger.info("CAMPAIGN_START", message=f"Campaign config loaded from {config_path}")

    def run(self, group_filter: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        if not self._config:
            self.load_campaign(str(self._config_path))
            
        tests = self._config.get("tests", [])
        campaign_name = self._config.get("campaign_name", "Unnamed Campaign")

        tests_sorted = sorted(
            enumerate(tests), key=lambda x: (x[1].get("priority", 99), x[0])
        )

        model_path = self._config.get("model_class")
        model_cls = None
        if model_path:
            try:
                mod_name, cls_name = model_path.rsplit(".", 1)
                model_cls = getattr(importlib.import_module(mod_name), cls_name)
                logger.info("CAMPAIGN_START", message=f"MUT Class Loaded: {model_path}")
            except Exception as exc:
                logger.info("ERROR", message=f"Failed to load model_class {model_path}: {exc}")

        logger.info("CAMPAIGN_START", message=f"Starting campaign: {campaign_name}")
        campaign_start = time.time()

        for _idx, test_cfg in tests_sorted:
            test_id: str = test_cfg["id"]
            test_name: str = test_cfg.get("name", test_id)
            module_path: str = test_cfg["module"]
            depends_on: Optional[str] = test_cfg.get("depends_on")
            test_group: Optional[str] = test_cfg.get("group")

            if group_filter and test_group != group_filter:
                continue

            if not self._resolve_dependencies(self._results, test_cfg):
                self._results[test_id] = {
                    "name": test_name,
                    "verdict": "BLOCKED",
                    "duration_ms": 0,
                    "details": f"Blocked by dependency failure.",
                    "signals_in": [],
                    "signals_out": [],
                    "verdict_history": [],
                }
                logger.info("BLOCKED", test_id=test_id, message=f"Test {test_id} blocked.")
                continue

            # For Phase 1, we use MIL implementation
            stimulator = MILStimulator()
            measurement = MILMeasurement()
            verdict_engine = VerdictEngine()

            if model_cls:
                stimulator.model = model_cls()

            logger.info("TEST_START", test_id=test_id, test_name=test_name)
            start_ts = time.time()

            try:
                module = importlib.import_module(module_path)
                result: Dict[str, Any] = module.run(
                    stimulator, measurement, verdict_engine
                )
            except Exception as exc:
                logger.info("ERROR", test_id=test_id, message=f"Exception in {test_id}: {exc}")
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

            logger.info("TEST_END", test_id=test_id, duration_ms=duration_ms, verdict=result.get("verdict"))

        campaign_duration_s = time.time() - campaign_start
        self._print_summary(campaign_name, campaign_duration_s)
        Reporter().generate(self._results, "reports")
        logger.info("CAMPAIGN_END", campaign_name=campaign_name, duration_s=campaign_duration_s)
        return self._results

    def _resolve_dependencies(self, results: dict, test: dict) -> bool:
        depends_on = test.get("depends_on")
        if not depends_on:
            return True
        
        dep_list = [depends_on] if isinstance(depends_on, str) else depends_on
        for dep_id in dep_list:
            parent = results.get(dep_id, {})
            if parent.get("verdict", "UNKNOWN") in ("FAIL", "BLOCKED", "UNKNOWN"):
                return False
        return True

    def _print_summary(self, campaign_name: str, duration_s: float) -> None:
        total = len(self._results)
        pass_count = sum(1 for r in self._results.values() if r["verdict"] == "PASS")
        pass_rate = (pass_count / total * 100) if total else 0.0

        print("\n" + "=" * 72)
        print(f"  CAMPAIGN SUMMARY — {campaign_name}")
        print(f"  Duration: {duration_s:.2f}s   Pass rate: {pass_rate:.0f}%  ({pass_count}/{total})")
        print("=" * 72)
        print(f"  {'ID':<12} {'Name':<30} {'Verdict':<14} {'Duration (ms)'}")
        print("-" * 72)
        for test_id, res in self._results.items():
            verdict = res["verdict"]
            color = _VERDICT_COLOR.get(verdict, "")
            print(f"  {test_id:<12} {res['name']:<30} {color}{verdict:<14}{_RESET} {res['duration_ms']:.1f}")
        print("=" * 72 + "\n")
