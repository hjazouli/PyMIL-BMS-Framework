"""
test_cases/tc_013_imd_fault.py — Layer 2
ASPICE Level: SYS.4 Isolation
"""
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

def run(stimulator, measurement, verdict_engine) -> Dict[str, Any]:
    stimulator.reset()
    measurement.clear()
    verdict_engine.clear_history()

    mut = stimulator.model
    mut.reset(initial_soc_pct=50.0, timestep_s=1.0)

    # Pack Voltage 400V -> R_iso_min = 40kOhm
    stimulator.send("pack_voltage_V", 400.0)
    
    # 1. OK Status
    stimulator.send("isolation_resistance_ohm", 100000.0) # 100k > 1.5*40k
    out = mut.step(stimulator.stimulus_bus)
    verdict_engine.evaluate("IMD_Status_OK", 1.0, 1.0 if out["isolation_status"] == "OK" else 0.0, 0.0, 0.0)
    
    # 2. Warning Status
    stimulator.send("isolation_resistance_ohm", 50000.0) # 40k < 50k < 60k
    out = mut.step(stimulator.stimulus_bus)
    verdict_engine.evaluate("IMD_Status_WARNING", 1.0, 1.0 if out["isolation_status"] == "WARNING" else 0.0, 0.0, 0.0)
    
    # 3. Fault Status
    stimulator.send("isolation_resistance_ohm", 30000.0) # 30k < 40k
    # Needs 3 steps in Block 9 to set CONFIRMED? 
    # Actually IMD_fault triggers DTC_0x07 as an input to Block 9.
    for _ in range(3): out = mut.step(stimulator.stimulus_bus)
    
    verdict_engine.evaluate("IMD_Status_FAULT", 1.0, 1.0 if out["isolation_status"] == "FAULT" else 0.0, 0.0, 0.0)
    verdict_engine.evaluate("IMD_DTC_Confirmed", 1.0, 1.0 if out["dtc_registry"]["DTC_0x07"]["status"] == "CONFIRMED" else 0.0, 0.0, 0.0)

    return {
        "verdict": verdict_engine.get_overall_verdict(),
        "details": f"IMD verified. Isolation Status: {out['isolation_status']}. DTC_0x07: {out['dtc_registry']['DTC_0x07']['status']}",
        "signals_in": ["isolation_resistance_ohm"],
        "signals_out": ["isolation_status", "dtc_registry"]
    }
