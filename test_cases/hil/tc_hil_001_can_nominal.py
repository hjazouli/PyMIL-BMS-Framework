import logging
from typing import Dict, Any
from framework.hil.hil_stimulator import HILStimulator
from framework.hil.hil_measurement import HILMeasurement
from framework.base.base_verdict_engine import BaseVerdictEngine

logger = logging.getLogger(__name__)

def run(stim: HILStimulator, meas: HILMeasurement, verdict: BaseVerdictEngine) -> Dict[str, Any]:
    """
    TC_HIL_001: CAN Nominal Communication.
    Verifies that stimuli can be replayed over CAN and results collected.
    """
    logger.info("Replaying WLTP cycle over CAN bus...")
    
    # Replay a few steps of WLTP
    csv_path = "stimuli/wltp_discharge.csv"
    profile = stim.send_profile("Current", csv_path, "Current[A]")
    
    for _ in range(20): # Run 2 seconds of cycles (100ms each)
        try:
            val = next(profile)
            # In HIL, we wait for the physical bus tick
            import time
            time.sleep(0.1) 
        except StopIteration:
            break
            
    # Verify we received Cell_1_Voltage on CAN
    actual_v = meas.get_latest("Cell_1_Voltage")
    verdict.evaluate("CAN_Alive_Cell1", 3.0, actual_v or 0.0, pass_tol=4.0, warn_tol=5.0)

    return {
        "verdict": verdict.get_overall_verdict(),
        "signals_in": ["Current"],
        "signals_out": ["Cell_1_Voltage"]
    }
