from abc import ABC, abstractmethod

class BaseStimulator(ABC):
    """
    Abstract interface for all stimulator implementations.
    MIL: writes to internal dict.
    HIL: encodes and transmits CAN frames.
    Test cases must only depend on this interface — never on concrete implementations.
    """
    @abstractmethod
    def send(self, signal_name: str, value: float) -> None:
        """Send a single signal value to the MUT input."""
        pass

    @abstractmethod
    def send_profile(self, signal_name: str, csv_path: str, column: str) -> None:
        """Replay a full CSV column as a time series of signal values."""
        pass

    @abstractmethod
    def reset(self) -> None:
        """Clear all current stimuli."""
        pass

    @abstractmethod
    def get_stimulus_bus(self) -> dict:
        """Return current state of all stimuli as a dict."""
        pass
