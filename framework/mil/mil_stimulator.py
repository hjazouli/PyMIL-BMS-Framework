import csv
import logging
import time
from typing import Dict, Generator
from ..base.base_stimulator import BaseStimulator

logger = logging.getLogger(__name__)

class MILStimulator(BaseStimulator):
    """
    MIL implementation of Stimulator using an internal dictionary bus.
    """

    def __init__(self) -> None:
        self.stimulus_bus: Dict[str, float] = {}
        logger.debug("MILStimulator initialised — stimulus_bus is empty.")

    def send(self, signal_name: str, value: float) -> None:
        self.stimulus_bus[signal_name] = value
        logger.debug(
            "[%.6f] MIL_STIM | %-25s = %g",
            time.monotonic(),
            signal_name,
            value,
        )

    def send_profile(self, signal_name: str, csv_path: str, column: str) -> Generator[float, None, None]:
        with open(csv_path, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                value = float(row[column])
                self.send(signal_name, value)
                yield value

    def reset(self) -> None:
        self.stimulus_bus.clear()
        logger.debug("MILStimulator reset — stimulus_bus cleared.")

    def __repr__(self) -> str:
        return f"MILStimulator(bus_keys={list(self.stimulus_bus.keys())})"
