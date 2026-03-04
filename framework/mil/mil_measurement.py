from typing import Dict, List, Tuple
from ..base.base_measurement import BaseMeasurement
from ..shared.logger import logger

class MILMeasurement(BaseMeasurement):
    """
    MIL implementation of Measurement.
    Stores measurements in an in-memory dictionary.
    """

    def __init__(self) -> None:
        """Initialize the MIL measurement storage."""
        self._data: Dict[str, List[Tuple[float, float]]] = {}
        logger.info("TEST_START", message="MILMeasurement store initialized.")

    def record(self, signal_name: str, value: float, timestamp: float) -> None:
        """
        Record a signal value at a specific timestamp.
        
        Args:
            signal_name: Name of the measured signal.
            value: Measured numeric value.
            timestamp: Simulation timestamp of the measurement.
        """
        self._data.setdefault(signal_name, []).append((timestamp, value))
        logger.info("SIGNAL_MEASURED", signal_name=signal_name, value=value, timestamp=timestamp)

    def get_latest(self, signal_name: str) -> float:
        """
        Get the most recent value for a signal.
        
        Args:
            signal_name: Name of the signal to retrieve.
            
        Returns:
            float: The latest recorded value, or 0.0 if not found.
        """
        series = self._data.get(signal_name)
        if not series:
            return 0.0
        return series[-1][1]

    def get_series(self, signal_name: str) -> List[Tuple[float, float]]:
        """
        Get the full time series of (timestamp, value) pairs for a signal.
        
        Args:
            signal_name: Name of the signal.
            
        Returns:
            List[Tuple[float, float]]: List of (timestamp, value) tuples.
        """
        return self._data.get(signal_name, [])

    def clear(self) -> None:
        """Reset all recorded measurements."""
        self._data.clear()
        logger.info("TEST_START", message="MILMeasurement store cleared.")

    def __repr__(self) -> str:
        summary = {k: len(v) for k, v in self._data.items()}
        return f"MILMeasurement(signals={summary})"
