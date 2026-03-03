import logging
from typing import Dict, List, Optional, Tuple
from ..base.base_measurement import BaseMeasurement

logger = logging.getLogger(__name__)

class MILMeasurement(BaseMeasurement):
    """
    MIL implementation of Measurement using in-memory dictionary.
    """

    def __init__(self) -> None:
        self._data: Dict[str, List[Tuple[float, float]]] = {}
        logger.debug("MILMeasurement store initialised.")

    def record(self, signal_name: str, value: float, timestamp: float) -> None:
        self._data.setdefault(signal_name, []).append((timestamp, value))
        logger.debug(
            "[t=%.3fs] MIL_MEAS | %-30s = %g",
            timestamp,
            signal_name,
            value,
        )

    def get_latest(self, signal_name: str) -> Optional[float]:
        series = self._data.get(signal_name)
        if not series:
            return None
        return series[-1][1]

    def get_series(self, signal_name: str) -> List[Tuple[float, float]]:
        return self._data.get(signal_name, [])

    def get_values(self, signal_name: str) -> List[float]:
        return [v for _, v in self.get_series(signal_name)]

    def available_signals(self) -> List[str]:
        return list(self._data.keys())

    def clear(self) -> None:
        self._data.clear()
        logger.debug("MILMeasurement store cleared.")

    def __repr__(self) -> str:
        summary = {k: len(v) for k, v in self._data.items()}
        return f"MILMeasurement(signals={summary})"
