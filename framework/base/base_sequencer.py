from abc import ABC, abstractmethod

class BaseSequencer(ABC):
    """
    Abstract campaign execution engine.
    Reads campaign YAML, resolves dependencies, executes test cases,
    collects verdicts, triggers reporter.
    """
    @abstractmethod
    def load_campaign(self, config_path: str) -> None:
        """Load campaign configuration from a YAML file."""
        pass

    @abstractmethod
    def run(self) -> dict:
        """Execute the full test campaign and return results."""
        pass

    @abstractmethod
    def _resolve_dependencies(self, results: dict, test: dict) -> bool:
        """Returns True if all dependencies passed, False if any BLOCKED."""
        pass
