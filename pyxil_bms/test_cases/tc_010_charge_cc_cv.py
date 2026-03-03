"""
test_cases/tc_010_charge_cc_cv.py — Layer 2
ASPICE Level: SYS.4 Charge Strategy
"""
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

def run(stimulator, measurement, verdict_engine) -> Dict[str, Any]:
    stimulator.reset()
    measurement.clear()
    verdict_engine.clear_history()

    mut = stimulator.model
    # Start IDLE at 98%
    mut.reset(initial_soc_pct=98.0, timestep_s=1.0)

    # 1. Request Charge
    stimulator.send("charging_requested", True)
    stimulator.send("pack_voltage_V", 24.0) # V_cell = 4.0
    stimulator.send("cell_temperatures", [25.0]*6)
    
    out = mut.step(stimulator.stimulus_bus)
    verdict_engine.evaluate("State_CC", 1.0, 1.0 if out["charge_state"] == "CC" else 0.0, 0.0, 0.0)
    
    # 2. Ramp voltage to CV trigger (4.15 * 6 = 24.9)
    stimulator.send("pack_voltage_V", 25.0)
    out = mut.step(stimulator.stimulus_bus)
    verdict_engine.evaluate("State_CV", 1.0, 1.0 if out["charge_state"] == "CV" else 0.0, 0.0, 0.0)
    
    # 3. Drop current below cutoff (0.05 * 100 = 5A)
    stimulator.send("pack_current_A", 2.0)
    out = mut.step(stimulator.stimulus_bus)
    verdict_engine.evaluate("State_COMPLETE", 1.0, 1.0 if out["charge_state"] == "COMPLETE" else 0.0, 0.0, 0.0)

    return {
        "verdict": verdict_engine.get_overall_verdict(),
        "details": f"Charge SM transitions verified: CC -> CV -> COMPLETE. Final target current: {out['charge_current_target_A']}A",
        "signals_in": ["charging_requested", "pack_voltage_V"],
        "signals_out": ["charge_state"]
    }
