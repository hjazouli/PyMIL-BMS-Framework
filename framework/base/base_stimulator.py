from abc import ABC, abstractmethod
from typing import Dict, Generator, Any

class BaseStimulator(ABC):
    """Abstract base class for signal stimulation."""
    
    @abstractmethod
    def send(self, signal_name: str, value: float) -> None:
        """Write a single scalar value onto the stimulus bus."""
        pass

    @abstractmethod
    def send_profile(self, signal_name: str, csv_path: str, column: str) -> Generator[float, None, None]:
        """Replay a CSV column as a time-series of signal values."""
        pass

    @abstractmethod
    def reset(self) -> None:
        """Clear all signals from the stimulus bus."""
        pass
