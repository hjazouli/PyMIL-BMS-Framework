from abc import ABC, abstractmethod

class BaseReporter(ABC):
    """
    Abstract report generator.
    Takes campaign results dict and produces a self-contained HTML report.
    """
    @abstractmethod
    def generate(self, results: dict, output_dir: str) -> str:
        """Returns path to generated report file."""
        pass
