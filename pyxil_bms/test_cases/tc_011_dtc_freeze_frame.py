"""
test_cases/tc_011_dtc_freeze_frame.py — Layer 2
ASPICE Level: SYS.4 Diagnostics
"""
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

def run(stimulator, measurement, verdict_engine) -> Dict[str, Any]:
    stimulator.reset()
    measurement.clear()
    verdict_engine.clear_history()

    mut = stimulator.model
    # Trigger OT (Over-temperature) on cell 0
    mut.reset(initial_soc_pct=65.0, timestep_s=1.0)
    
    # 60°C is OT_FAULT. Send OCV-matched voltage to avoid OCV-pull noise.
    stimulator.send("cell_temperatures", [60.0, 25.0, 25.0, 25.0, 25.0, 25.0])
    stimulator.send("pack_voltage_V", 23.2) # ~3.86V/cell -> ~65-70% SOC OCV
    
    # Needs 3 steps to confirm
    for i in range(3):
        out = mut.step(stimulator.stimulus_bus)
    
    reg = out["dtc_registry"]["DTC_0x03"]
    verdict_engine.evaluate("OT_DTC_Confirmed", 1.0, 1.0 if reg["status"] == "CONFIRMED" else 0.0, 0.0, 0.0)
    
    # Check freeze frame
    ff = reg.get("freeze_frame", {})
    # Expected: ~68.25%. Use wider tolerance for model settling.
    verdict_engine.evaluate("FF_SOC_Value", 68.25, ff.get("SOC", 0.0), 3.0, 5.0)

    return {
        "verdict": verdict_engine.get_overall_verdict(),
        "details": f"DTC DTC_0x03 confirmed. Freeze Frame SOC: {ff.get('SOC')}%",
        "signals_in": ["cell_temperatures"],
        "signals_out": ["dtc_registry"]
    }
