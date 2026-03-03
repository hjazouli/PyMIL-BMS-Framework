from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

class BaseMeasurement(ABC):
    """Abstract base class for signal measurement and recording."""

    @abstractmethod
    def record(self, signal_name: str, value: float, timestamp: float) -> None:
        """Append a measured value for a given signal."""
        pass

    @abstractmethod
    def get_latest(self, signal_name: str) -> Optional[float]:
        """Return the most recently recorded value for signal_name."""
        pass

    @abstractmethod
    def get_series(self, signal_name: str) -> List[Tuple[float, float]]:
        """Return the full [(timestamp, value), ...] series for signal_name."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Reset all recorded measurements."""
        pass
