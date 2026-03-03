import logging
import time
from typing import Dict, Any
from framework.hil.hil_stimulator import HILStimulator
from framework.hil.hil_measurement import HILMeasurement
from framework.base.base_verdict_engine import BaseVerdictEngine
from framework.hil.hil_fault_injector import HILFaultInjector

logger = logging.getLogger(__name__)

def run(stim: HILStimulator, meas: HILMeasurement, verdict: BaseVerdictEngine) -> Dict[str, Any]:
    """
    TC_HIL_003: BusOff Recovery.
    Verifies autonomous recovery after a bus-off condition.
    """
    injector = HILFaultInjector()
    
    logger.info("Simulating CAN Bus-Off condition...")
    injector.inject_bus_off()
    
    time.sleep(1.0) # Wait for recovery
    
    # Check if messages have resumed
    actual_v = meas.get_latest("Cell_1_Voltage")
    verdict.evaluate("Bus_Recovery", 3.0, actual_v or 0.0, pass_tol=1.0, warn_tol=2.0)

    return {"verdict": verdict.get_overall_verdict()}
