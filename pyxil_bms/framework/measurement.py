"""
framework/measurement.py — Layer 1

Responsibility:
    Captures and stores output signals emitted by the MUT.
    Provides point-in-time and full time-series access to recorded data.
    Completely MUT-agnostic: signal names are always passed as strings.
"""

import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class Measurement:
    """
    In-memory buffer for MUT output signals.

    Storage schema:
        {signal_name: [(timestamp_s, value), ...]}

    All signal names are runtime strings — no names are hardcoded inside
    this class, ensuring the framework is algorithm-agnostic.
    """

    def __init__(self) -> None:
        self._data: Dict[str, List[Tuple[float, float]]] = {}
        logger.debug("Measurement store initialised.")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def record(self, signal_name: str, value: float, timestamp: float) -> None:
        """
        Append a measured value for a given signal.

        Args:
            signal_name: Runtime string key (e.g. 'SOC_estimated').
            value:       Numeric output value from the MUT.
            timestamp:   Simulation time in seconds at which value was sampled.
        """
        self._data.setdefault(signal_name, []).append((timestamp, value))
        logger.debug(
            "[t=%.3fs] MEASURE  | %-30s = %g",
            timestamp,
            signal_name,
            value,
        )

    def get_latest(self, signal_name: str) -> Optional[float]:
        """
        Return the most recently recorded value for *signal_name*.

        Returns:
            The latest float value, or None if the signal has not been recorded.
        """
        series = self._data.get(signal_name)
        if not series:
            logger.warning("get_latest: no data for signal '%s'.", signal_name)
            return None
        return series[-1][1]

    def get_series(self, signal_name: str) -> List[Tuple[float, float]]:
        """
        Return the full [(timestamp, value), ...] series for *signal_name*.

        Returns:
            List of (timestamp, value) tuples (empty list if no data).
        """
        return self._data.get(signal_name, [])

    def get_values(self, signal_name: str) -> List[float]:
        """
        Convenience: return only the value component of the time series.

        Returns:
            List of float values in chronological order.
        """
        return [v for _, v in self.get_series(signal_name)]

    def available_signals(self) -> List[str]:
        """Return list of all signal names that have recorded data."""
        return list(self._data.keys())

    def clear(self) -> None:
        """Reset all recorded measurements."""
        self._data.clear()
        logger.debug("Measurement store cleared.")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def __repr__(self) -> str:  # pragma: no cover
        summary = {k: len(v) for k, v in self._data.items()}
        return f"Measurement(signals={summary})"
