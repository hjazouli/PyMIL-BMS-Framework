"""
test_cases/tc_003_soh_degradation.py — Layer 2
ASPICE Level: SYS.4 Estimation
"""
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

def run(stimulator, measurement, verdict_engine) -> Dict[str, Any]:
    stimulator.reset()
    measurement.clear()
    verdict_engine.clear_history()

    mut = stimulator.model
    mut.reset(initial_soc_pct=95.0, timestep_s=1.0)

    # Simulate aging: drop capacity to 80Ah
    stimulator.send("capacity_Ah", 80.0)
    stimulator.send("pack_current_A", 0.0)
    stimulator.send("pack_voltage_V", 400.0)
    
    outputs = mut.step(stimulator.stimulus_bus)
    soh = outputs["SOH_estimated"]
    
    # We need 3 steps for CONFIRMED in Block 9
    for _ in range(3): outputs = mut.step(stimulator.stimulus_bus)
    
    reg = outputs.get("dtc_registry", {})
    status = reg.get("DTC_0x05", {}).get("status", "INACTIVE")
    
    verdict_engine.evaluate("SOH_80", 0.8, soh, 0.01, 0.02)
    verdict_engine.evaluate("DTC_SOH_Status", 1.0, 1.0 if status == "CONFIRMED" else 0.0, 0.0, 0.0)

    return {
        "verdict": verdict_engine.get_overall_verdict(),
        "details": f"SOH Degradation detected: {soh:.2f} Status: {status}",
        "signals_in": ["capacity_Ah"],
        "signals_out": ["SOH_estimated"]
    }
