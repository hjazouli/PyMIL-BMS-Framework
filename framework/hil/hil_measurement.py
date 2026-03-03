import logging
import threading
import time
import can
import cantools
from typing import Dict, List, Optional, Tuple
from ..base.base_measurement import BaseMeasurement

logger = logging.getLogger(__name__)

class HILMeasurement(BaseMeasurement):
    """
    HIL implementation of Measurement listening to CAN frames in the background.
    """

    def __init__(self, interface: str = "vcan0", dbc_path: str = "can/bms_pack.dbc") -> None:
        self._interface = interface
        self._db = cantools.database.load_file(dbc_path)
        self._data: Dict[str, List[Tuple[float, float]]] = {}
        
        self._stop_event = threading.Event()
        self._bus = can.interface.Bus(channel=interface, interface="socketcan")
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        
        logger.info("HILMeasurement listening on %s", interface)

    def _listen_loop(self) -> None:
        while not self._stop_event.is_set():
            msg = self._bus.recv(0.1)
            if msg:
                try:
                    # Try to decode the message
                    msg_def = None
                    try:
                        msg_def = self._db.get_message_by_frame_id(msg.arbitration_id)
                    except KeyError:
                        continue
                    
                    decoded = msg_def.decode(msg.data)
                    timestamp = time.perf_counter() # Use wall-clock time for HIL
                    
                    for sig_name, value in decoded.items():
                        self.record(sig_name, value, timestamp)
                except Exception as e:
                    logger.error("HILMeasurement decode error: %s", e)

    def record(self, signal_name: str, value: float, timestamp: float) -> None:
        self._data.setdefault(signal_name, []).append((timestamp, value))
        logger.debug("[%.3fs] HIL_MEAS | %-30s = %g", timestamp, signal_name, value)

    def get_latest(self, signal_name: str) -> Optional[float]:
        series = self._data.get(signal_name)
        return series[-1][1] if series else None

    def get_series(self, signal_name: str) -> List[Tuple[float, float]]:
        return self._data.get(signal_name, [])

    def clear(self) -> None:
        self._data.clear()

    def stop(self) -> None:
        self._stop_event.set()
        self._thread.join(2.0)
        self._bus.shutdown()
