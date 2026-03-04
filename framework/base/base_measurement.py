from abc import ABC, abstractmethod

class BaseMeasurement(ABC):
    """
    Abstract interface for all measurement implementations.
    MIL: reads from MUT output dict.
    HIL: decodes incoming CAN frames.
    """
    @abstractmethod
    def record(self, signal_name: str, value: float, timestamp: float) -> None:
        """Record a signal value at a specific timestamp."""
        pass

    @abstractmethod
    def get_latest(self, signal_name: str) -> float:
        """Get the most recent value for a signal."""
        pass

    @abstractmethod
    def get_series(self, signal_name: str) -> list:
        """Get the full time series of (timestamp, value) pairs for a signal."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Reset all recorded measurements."""
        pass
