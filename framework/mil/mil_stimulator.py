import csv
import time
from typing import Dict
from ..base.base_stimulator import BaseStimulator
from ..shared.logger import logger

class MILStimulator(BaseStimulator):
    """
    MIL implementation of Stimulator.
    Writes signal values to an internal dictionary bus.
    """

    def __init__(self) -> None:
        """Initialize the MIL stimulator with an empty stimulus bus."""
        self.stimulus_bus: Dict[str, float] = {}
        logger.info("TEST_START", message="MILStimulator initialized.")

    def send(self, signal_name: str, value: float) -> None:
        """
        Send a single signal value to the internal stimulus bus.
        
        Args:
            signal_name: Name of the signal to update.
            value: Numeric value to set.
        """
        self.stimulus_bus[signal_name] = value
        logger.info("STIMULI_SENT", signal_name=signal_name, value=value)

    def send_profile(self, signal_name: str, csv_path: str, column: str) -> None:
        """
        Replay a full CSV column as a time series of signal values.
        In MIL, this happens synchronously without timing constraints.
        
        Args:
            signal_name: Name of the signal to update.
            csv_path: Path to the CSV file containing the profile.
            column: Name of the column in the CSV to use.
        """
        with open(csv_path, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                value = float(row[column])
                self.send(signal_name, value)

    def reset(self) -> None:
        """Clear all current stimuli from the internal bus."""
        self.stimulus_bus.clear()
        # No specific event type for reset in logger spec, but we can log a message
        logger.info("TEST_START", message="MILStimulator stimulus bus reset.")

    def get_stimulus_bus(self) -> Dict[str, float]:
        """
        Return current state of all stimuli as a dictionary.
        
        Returns:
            Dict[str, float]: The internal stimulus bus.
        """
        return self.stimulus_bus

    def __repr__(self) -> str:
        return f"MILStimulator(bus_keys={list(self.stimulus_bus.keys())})"
