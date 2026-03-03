"""
test_cases/tc_006_thermal_derating.py — Layer 2
ASPICE Level: SYS.4 Derating
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

    # 50°C -> Cooling HIGH, DF = 0.60
    stimulator.send("cell_temperatures", [50.0]*6)
    stimulator.send("pack_current_A", 10.0)
    
    out = mut.step(stimulator.stimulus_bus)
    
    verdict_engine.evaluate("Cooling_Request_50", 1.0, 1.0 if out["cooling_request"] == "HIGH" else 0.0, 0.0, 0.0)
    verdict_engine.evaluate("Thermal_DF_50", 0.60, out["thermal_derating_factor"], 0.01, 0.05)
    
    # Check SOP reduction (nominal charge 150kW * 0.60 = 90kW)
    # Actually SOP is also SOH scaled. SOH=1.0. 
    # 150 * 0.6 = 90.0
    verdict_engine.evaluate("SOP_Charge_Derated", 90.0, out["SOP_charge_kW"], 1.0, 5.0)

    return {
        "verdict": verdict_engine.get_overall_verdict(),
        "details": f"Thermal derating verified at 50°C. Cooling: {out['cooling_request']} SOP: {out['SOP_charge_kW']}kW",
        "signals_in": ["cell_temperatures"],
        "signals_out": ["cooling_request", "SOP_charge_kW"]
    }
