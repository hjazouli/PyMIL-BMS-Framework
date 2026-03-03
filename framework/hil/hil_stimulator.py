import logging
import can
import cantools
from typing import Dict, Generator, Optional
from ..base.base_stimulator import BaseStimulator

logger = logging.getLogger(__name__)

class HILStimulator(BaseStimulator):
    """
    HIL implementation of Stimulator using CAN bus via python-can.
    """

    def __init__(self, interface: str = "vcan0", dbc_path: str = "can/bms_pack.dbc") -> None:
        self._interface = interface
        try:
            self._db = cantools.database.load_file(dbc_path)
            self._bus = can.interface.Bus(channel=interface, interface="socketcan")
            logger.info("HILStimulator connected to %s with DBC %s", interface, dbc_path)
        except Exception as e:
            logger.error("Failed to initialize HILStimulator: %s", e)
            raise

    def send(self, signal_name: str, value: float) -> None:
        """
        Encodes and transmits a CAN frame containing the signal.
        """
        try:
            # Find message containing this signal
            msg_def = None
            for msg in self._db.messages:
                if any(sig.name == signal_name for sig in msg.signals):
                    msg_def = msg
                    break
            
            if not msg_def:
                logger.error("Signal %s not found in DBC", signal_name)
                return

            # Note: In a real HIL we might need to keep track of ALL signals in the message
            # For this demo, we'll assume we can send a frame with just this signal or defaults
            data = msg_def.encode({signal_name: value})
            message = can.Message(arbitration_id=msg_def.frame_id, data=data, is_extended_id=msg_def.is_extended_frame)
            self._bus.send(message)
            
            logger.debug(
                "HIL_STIM | %s | ID: 0x%X | %s = %g",
                self._interface,
                msg_def.frame_id,
                signal_name,
                value,
            )
        except Exception as e:
            logger.error("HILStimulator.send error: %s", e)

    def send_profile(self, signal_name: str, csv_path: str, column: str) -> Generator[float, None, None]:
        """
        Paced by the caller (RealtimeScheduler).
        """
        import csv
        with open(csv_path, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                value = float(row[column])
                self.send(signal_name, value)
                yield value

    def reset(self) -> None:
        """Not applicable for HIL bus reset in this implementation snippet."""
        pass
