from abc import ABC, abstractmethod

class BaseVerdictEngine(ABC):
    """
    Abstract interface for verdict evaluation.
    Concrete implementation is shared between MIL and HIL — only the
    signal source changes, not the verdict logic.
    """
    @abstractmethod
    def evaluate(self, signal_name: str, expected: float, actual: float,
                 pass_tol: float, warn_tol: float) -> str:
        """Evaluate a single signal value against expectations and tolerances."""
        pass

    @abstractmethod
    def evaluate_series(self, signal_name: str, expected_series: list,
                        actual_series: list, pass_tol: float, warn_tol: float) -> str:
        """Evaluate a full series of signal values."""
        pass
