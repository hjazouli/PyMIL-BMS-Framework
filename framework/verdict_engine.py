from typing import List
from .base.base_verdict_engine import BaseVerdictEngine
from .shared.logger import logger

# Ordered worst → best so comparisons are straightforward.
_VERDICT_RANK = {"FAIL": 0, "INCONCLUSIVE": 1, "PASS": 2, "BLOCKED": -1}

def _worst(a: str, b: str) -> str:
    """Return the worse of two verdict strings."""
    return a if _VERDICT_RANK.get(a, -1) <= _VERDICT_RANK.get(b, -1) else b

class VerdictEngine(BaseVerdictEngine):
    """
    Concrete implementation of the three-zone tolerance verdict system.
    Compatible with ASPICE SYS.4 / SYS.5 test-level requirements.
    """

    def __init__(self) -> None:
        self._history: List[dict] = []
        logger.info("TEST_START", message="VerdictEngine initialized.")

    def evaluate(
        self,
        signal_name: str,
        expected: float,
        actual: float,
        pass_tol: float,
        warn_tol: float,
    ) -> str:
        if warn_tol < pass_tol:
            raise ValueError(
                f"warn_tol ({warn_tol}) must be >= pass_tol ({pass_tol})"
            )

        delta = abs(actual - expected)

        if delta <= pass_tol:
            verdict = "PASS"
            band = f"<= pass_tol ({pass_tol})"
        elif delta <= warn_tol:
            verdict = "INCONCLUSIVE"
            band = f"({pass_tol}, {warn_tol}]"
        else:
            verdict = "FAIL"
            band = f"> warn_tol ({warn_tol})"

        record = {
            "signal": signal_name,
            "expected": expected,
            "actual": actual,
            "delta": delta,
            "band": band,
            "verdict": verdict,
        }
        self._history.append(record)

        logger.info(
            "VERDICT",
            signal_name=signal_name,
            expected=expected,
            actual=actual,
            delta=delta,
            band=band,
            verdict=verdict
        )
        return verdict

    def evaluate_series(
        self,
        signal_name: str,
        expected_series: List[float],
        actual_series: List[float],
        pass_tol: float,
        warn_tol: float,
    ) -> str:
        n = min(len(expected_series), len(actual_series))
        if n == 0:
            logger.info("ERROR", message=f"evaluate_series: empty series for '{signal_name}'.")
            return "INCONCLUSIVE"

        worst = "PASS"
        for i, (exp, act) in enumerate(
            zip(expected_series[:n], actual_series[:n])
        ):
            v = self.evaluate(
                f"{signal_name}[{i}]", exp, act, pass_tol, warn_tol
            )
            worst = _worst(worst, v)
            if worst == "FAIL":
                break

        logger.info("VERDICT", message=f"SERIES VERDICT | {signal_name} | n={n} worst={worst}")
        return worst

    def get_overall_verdict(self) -> str:
        if not self._history:
            return "PASS"
        overall = "PASS"
        for rec in self._history:
            overall = _worst(overall, rec["verdict"])
        return overall

    def get_history(self) -> List[dict]:
        return list(self._history)

    def clear_history(self) -> None:
        self._history.clear()
        logger.info("TEST_START", message="VerdictEngine history cleared.")
