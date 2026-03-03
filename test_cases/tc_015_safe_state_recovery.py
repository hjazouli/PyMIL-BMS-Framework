"""
test_cases/tc_015_safe_state_recovery.py — Layer 2
ASPICE Level: SYS.5 Recovery
"""
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

def run(stimulator, measurement, verdict_engine) -> Dict[str, Any]:
    stimulator.reset()
    measurement.clear()
    verdict_engine.clear_history()

    mut = stimulator.model
    # 1. Enter Safe State via UV fault
    mut.reset(initial_soc_pct=50.0, timestep_s=1.0)
    stimulator.send("cell_voltages", [2.5]*6)
    for _ in range(3): out = mut.step(stimulator.stimulus_bus)
    verdict_engine.evaluate("Trigger_SafeState", 1.0, 1.0 if out["SAFE_STATE"] else 0.0, 0.0, 0.0)

    # 2. Clear fault but no reset requested
    stimulator.send("cell_voltages", [3.7]*6)
    out = mut.step(stimulator.stimulus_bus)
    verdict_engine.evaluate("SafeState_Retained_Without_Reset", 1.0, 1.0 if out["SAFE_STATE"] else 0.0, 0.0, 0.0)

    # 3. Request Reset
    stimulator.send("reset_requested", True)
    out = mut.step(stimulator.stimulus_bus)
    
    # After reset and with fault gone, SAFE_STATE should be 0
    verdict_engine.evaluate("SafeState_Cleared_After_Reset", 0.0, 1.0 if out["SAFE_STATE"] else 0.0, 0.0, 0.0)

    return {
        "verdict": verdict_engine.get_overall_verdict(),
        "details": f"Safe state recovery verified. Final SAFE_STATE: {out['SAFE_STATE']}",
        "signals_in": ["reset_requested", "cell_voltages"],
        "signals_out": ["SAFE_STATE"]
    }
