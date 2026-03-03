"""
framework/base/base_verdict_engine.py — Layer 1

Responsibility:
    Implements a three-zone tolerance verdict system compatible with
    ASPICE SYS.4 / SYS.5 test-level requirements.

Zones:
    |delta| <= pass_tol            → "PASS"
    pass_tol < |delta| <= warn_tol → "INCONCLUSIVE"
    |delta| > warn_tol             → "FAIL"
"""

import logging
from typing import List

logger = logging.getLogger(__name__)

# Ordered worst → best so comparisons are straightforward.
_VERDICT_RANK = {"FAIL": 0, "INCONCLUSIVE": 1, "PASS": 2, "BLOCKED": -1}


def _worst(a: str, b: str) -> str:
    """Return the worse of two verdict strings."""
    return a if _VERDICT_RANK.get(a, -1) <= _VERDICT_RANK.get(b, -1) else b


class BaseVerdictEngine:
    """
    Three-zone tolerance verdict engine.

    Every evaluation is logged with full signal context (name, expected,
    actual, delta, tolerance band, verdict) so reports are fully traceable.
    No signal names are hardcoded — all are passed as runtime strings.
    """

    def __init__(self) -> None:
        self._history: List[dict] = []
        logger.debug("VerdictEngine initialised.")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def evaluate(
        self,
        signal_name: str,
        expected: float,
        actual: float,
        pass_tol: float,
        warn_tol: float,
    ) -> str:
        """
        Evaluate a single-point measurement against a reference value.

        Args:
            signal_name: Runtime signal identifier (for logging / tracing).
            expected:    Reference / golden value.
            actual:      Measured value from the MUT.
            pass_tol:    Absolute tolerance for PASS verdict.
            warn_tol:    Absolute tolerance for INCONCLUSIVE verdict
                         (must be >= pass_tol).

        Returns:
            "PASS" | "INCONCLUSIVE" | "FAIL"
        """
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
            "VERDICT  | %-30s | expected=%g actual=%g delta=%g band=%s → %s",
            signal_name,
            expected,
            actual,
            delta,
            band,
            verdict,
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
        """
        Evaluate two parallel time series and return the *worst* verdict.

        Mismatched lengths are handled by truncating to the shorter series.

        Args:
            signal_name:     Runtime signal identifier.
            expected_series: Reference values (one per timestep).
            actual_series:   MUT output values (one per timestep).
            pass_tol:        Absolute tolerance for PASS.
            warn_tol:        Absolute tolerance for INCONCLUSIVE.

        Returns:
            Worst verdict across all timesteps: "PASS" | "INCONCLUSIVE" | "FAIL"
        """
        n = min(len(expected_series), len(actual_series))
        if n == 0:
            logger.warning("evaluate_series: empty series for '%s'.", signal_name)
            return "INCONCLUSIVE"

        if len(expected_series) != len(actual_series):
            logger.warning(
                "evaluate_series: length mismatch for '%s' "
                "(expected=%d, actual=%d) — truncating to %d.",
                signal_name,
                len(expected_series),
                len(actual_series),
                n,
            )

        worst = "PASS"
        for i, (exp, act) in enumerate(
            zip(expected_series[:n], actual_series[:n])
        ):
            v = self.evaluate(
                f"{signal_name}[{i}]", exp, act, pass_tol, warn_tol
            )
            worst = _worst(worst, v)
            if worst == "FAIL":
                # Short-circuit: can't get worse than FAIL.
                break

        logger.info(
            "SERIES VERDICT | %-30s | n=%d worst=%s", signal_name, n, worst
        )
        return worst

    def get_overall_verdict(self) -> str:
        """Return the worst verdict recorded in the history."""
        if not self._history:
            return "PASS"
        overall = "PASS"
        for rec in self._history:
            overall = _worst(overall, rec["verdict"])
        return overall

    def get_history(self) -> List[dict]:
        """Return a copy of all individual evaluation records."""
        return list(self._history)

    def clear_history(self) -> None:
        """Reset evaluation history (useful between test cases)."""
        self._history.clear()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def __repr__(self) -> str:  # pragma: no cover
        return f"VerdictEngine(evaluations={len(self._history)})"
