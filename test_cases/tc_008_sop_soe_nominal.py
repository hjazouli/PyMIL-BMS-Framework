"""
test_cases/tc_008_sop_soe_nominal.py — Layer 2
ASPICE Level: SYS.4 Performance
"""
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

def run(stimulator, measurement, verdict_engine) -> Dict[str, Any]:
    stimulator.reset()
    measurement.clear()
    verdict_engine.clear_history()

    mut = stimulator.model
    # Start at 90% SOC, 100Ah
    mut.reset(initial_soc_pct=90.0, timestep_s=1.0)

    # Inputs for Block 5&6
    stimulator.send("pack_voltage_V", 400.0)
    stimulator.send("SOC_estimated", 90.0)
    stimulator.send("SOH_estimated", 1.0)
    stimulator.send("cell_temperatures", [25.0]*6) # DF = 1.0
    
    out = mut.step(stimulator.stimulus_bus)
    
    # SOE: 90% of 100Ah @ 400V = 90Ah * 400V = 36000Wh = 36kWh
    # Block 6: energy = SOC/100 * capacity * volt / 1000
    verdict_engine.evaluate("SOE_Energy", 36.0, out["SOE_kWh"], 0.5, 1.0)
    
    # SOP: Nominal 250kW discharge, 150kW charge
    # Since SOC > 90% (Wait, 90.0 exactly?)
    # Block 5: if soc > 90: p_chg *= (1 - (soc - 90) / 10.0)
    # At 90.0, factor is 1.0. 
    verdict_engine.evaluate("SOP_Discharge", 250.0, out["SOP_discharge_kW"], 5.0, 10.0)
    verdict_engine.evaluate("SOP_Charge", 150.0, out["SOP_charge_kW"], 5.0, 10.0)
    
    # Range km: 36kWh / 0.180 = 200km
    verdict_engine.evaluate("Range_Estimate", 200.0, out["estimated_range_km"], 5.0, 10.0)

    return {
        "verdict": verdict_engine.get_overall_verdict(),
        "details": f"Energy/Power estimation checks: {out['SOE_kWh']}kWh, Range {out['estimated_range_km']}km",
        "signals_in": ["pack_voltage_V"],
        "signals_out": ["SOE_kWh", "SOP_discharge_kW", "estimated_range_km"]
    }
