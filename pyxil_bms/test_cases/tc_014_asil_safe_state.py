"""
test_cases/tc_014_asil_safe_state.py — Layer 2
ASPICE Level: SYS.5 Safety
"""
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

def run(stimulator, measurement, verdict_engine) -> Dict[str, Any]:
    stimulator.reset()
    measurement.clear()
    verdict_engine.clear_history()

    mut = stimulator.model
    # Test ASIL-D fault: Cell UV Fault
    mut.reset(initial_soc_pct=50.0, timestep_s=1.0)

    # 1. Closed state initially (Allow precharge steps)
    stimulator.send("contactor_command", True)
    stimulator.send("hv_bus_voltage_V", 395.0) # Match pack voltage ~400V
    stimulator.send("pack_voltage_V", 400.0)
    
    # Run a few steps to transition OPEN -> PRECHARGE -> CLOSED
    for _ in range(5): out = mut.step(stimulator.stimulus_bus)
    
    verdict_engine.evaluate("Safe_Start_Contactor", 1.0, 1.0 if out["contactor_state"] == "CLOSED" else 0.0, 0.0, 0.0)

    # 2. Trigger UV Fault (< 2.80V)
    stimulator.send("cell_voltages", [2.5, 3.7, 3.7, 3.7, 3.7, 3.7])
    
    # Fault Tolerance Time: within 3 steps
    for i in range(3):
        out = mut.step(stimulator.stimulus_bus)
    
    # Check Safe State
    verdict_engine.evaluate("SAFE_STATE_Active", 1.0, 1.0 if out["SAFE_STATE"] else 0.0, 0.0, 0.0)
    verdict_engine.evaluate("Contactor_OPEN_on_SafeState", 1.0, 1.0 if out["contactor_state"] == "OPEN" else 0.0, 0.0, 0.0)
    verdict_engine.evaluate("SOP_Zero_on_SafeState", 0.0, out["SOP_discharge_kW"], 0.0, 0.0)
    verdict_engine.evaluate("Cooling_EMERGENCY", 1.0, 1.0 if out["cooling_request"] == "EMERGENCY" else 0.0, 0.0, 0.0)

    return {
        "verdict": verdict_engine.get_overall_verdict(),
        "details": f"ASIL-D Safe State verified. Reason: {out.get('safe_state_reason')}. Contactor: {out['contactor_state']}",
        "signals_in": ["cell_voltages"],
        "signals_out": ["SAFE_STATE", "contactor_state", "SOP_discharge_kW"]
    }
