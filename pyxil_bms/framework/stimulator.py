"""
framework/stimulator.py — Layer 1

Responsibility:
    Feeds input signals into the MUT via an internal stimulus_bus dictionary.
    The Stimulator is completely MUT-agnostic: it knows nothing about what
    the MUT does with the signals it receives.
"""

import csv
import logging
import time
from typing import Dict

logger = logging.getLogger(__name__)


class Stimulator:
    """
    Manages and delivers input stimuli to the MUT stimulus bus.

    The stimulus_bus dict is the single handoff point between the framework
    and the MUT. At each simulation step the MUT reads from this dict.
    All signal names are runtime strings — no signal names are hardcoded
    inside this class.
    """

    def __init__(self) -> None:
        self.stimulus_bus: Dict[str, float] = {}
        logger.debug("Stimulator initialised — stimulus_bus is empty.")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def send(self, signal_name: str, value: float) -> None:
        """
        Write a single scalar value onto the stimulus bus.

        Args:
            signal_name: Runtime string key for the signal (e.g. 'current_A').
            value:       The numeric value to deliver to the MUT.
        """
        self.stimulus_bus[signal_name] = value
        logger.debug(
            "[%.6f] STIMULUS | %-25s = %g",
            time.monotonic(),
            signal_name,
            value,
        )

    def send_profile(self, signal_name: str, csv_path: str, column: str):
        """
        Generator: replay a CSV column as a time-series of signal values.

        Each call to next() yields the next row's value and writes it to
        the stimulus bus. The caller is responsible for iterating and
        advancing the simulation step.

        Args:
            signal_name: Key under which the value will appear on the bus.
            csv_path:    Absolute or relative path to the CSV file.
            column:      Column header name inside the CSV to read from.

        Yields:
            float: The value of *column* for the current row.
        """
        with open(csv_path, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                value = float(row[column])
                self.send(signal_name, value)
                yield value

    def reset(self) -> None:
        """Clear all signals from the stimulus bus."""
        self.stimulus_bus.clear()
        logger.debug("Stimulator reset — stimulus_bus cleared.")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def __repr__(self) -> str:  # pragma: no cover
        return f"Stimulator(bus_keys={list(self.stimulus_bus.keys())})"
