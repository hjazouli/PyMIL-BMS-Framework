"""
test_cases/tc_005_cell_ut_cold_start.py — Layer 2
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
    # Cold start: -10°C
    mut.reset(initial_soc_pct=90.0, timestep_s=1.0)
    
    stimulator.send("cell_temperatures", [-10.0]*6)
    stimulator.send("pack_current_A", 0.0)
    
    # Step
    out = mut.step(stimulator.stimulus_bus)
    
    # Expected: SOC_estimated should reflect temp factor for -10°C (~0.90)
    # 90.0 * 0.90 = 81.0
    verdict_engine.evaluate("Cold_SOC_Correction", 81.0, out["SOC_estimated"], 0.5, 1.0)
    
    # Thermal derating check
    # -10°C -> DF = 0.50
    verdict_engine.evaluate("Cold_Derating_Factor", 0.50, out["thermal_derating_factor"], 0.01, 0.05)
    
    # UT Warning check (-10°C is warning)
    verdict_engine.evaluate("UT_Warning_Active", 1.0, 1.0 if "WARNING" in out["cell_fault_severity"] else 0.0, 0.0, 0.0)

    return {
        "verdict": verdict_engine.get_overall_verdict(),
        "details": f"Cold start verified. SOC corrected to {out['SOC_estimated']}%. DF={out['thermal_derating_factor']}",
        "signals_in": ["cell_temperatures"],
        "signals_out": ["SOC_estimated", "thermal_derating_factor"]
    }
