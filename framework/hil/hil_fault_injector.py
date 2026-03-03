import logging
import can
import time
from typing import Optional

logger = logging.getLogger(__name__)

class HILFaultInjector:
    """
    Injects hardware and protocol level faults into the CAN bus.
    """

    def __init__(self, interface: str = "vcan0") -> None:
        self._interface = interface
        self._bus = can.interface.Bus(channel=interface, interface="socketcan")

    def inject_message_timeout(self, message_id: int, duration_ms: int) -> None:
        """
        Suppresses transmission of a message ID by sending an override or just logging for logic.
        In a real HIL, this would interact with the interface gateway.
        """
        logger.warning("F-INJECT | TIMEOUT | ID=0x%X | Duration=%dms", message_id, duration_ms)
        # Simulation logic: in this mock we just log and the test case handles it
        time.sleep(duration_ms / 1000.0)

    def inject_signal_spike(self, stimulator, signal_name: str, spike_value: float, duration_steps: int) -> None:
        """
        Overrides a signal with a spike for N steps.
        """
        logger.warning("F-INJECT | SPIKE | %s=%g | Duration=%d steps", signal_name, spike_value, duration_steps)
        for _ in range(duration_steps):
            stimulator.send(signal_name, spike_value)
            time.sleep(0.1) # Simulate step

    def inject_bus_off(self) -> None:
        """
        Simulates a bus-off condition.
        """
        logger.error("F-INJECT | BUS-OFF | Driving node into error passive...")
        # In a real setup, we'd send high-load traffic or error frames
        # For mock: send many high-priority empty frames
        for _ in range(100):
            msg = can.Message(arbitration_id=0x00, data=[0xFF]*8)
            self._bus.send(msg)
