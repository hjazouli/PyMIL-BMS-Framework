"""
test_cases/tc_004_cell_ov_detection.py — Layer 2
ASPICE Level: SYS.5 Diagnostics
"""
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

def run(stimulator, measurement, verdict_engine) -> Dict[str, Any]:
    stimulator.reset()
    measurement.clear()
    verdict_engine.clear_history()

    mut = stimulator.model
    mut.reset(initial_soc_pct=50.0, timestep_s=0.1)

    # Normal
    stimulator.send("cell_voltages", [3.7]*6)
    mut.step(stimulator.stimulus_bus)
    
    # OV Fault on cell 0
    stimulator.send("cell_voltages", [4.20, 3.7, 3.7, 3.7, 3.7, 3.7])
    
    # Step 1: PENDING
    out = mut.step(stimulator.stimulus_bus)
    verdict_engine.evaluate("OV_PENDING_1", 1.0, 1.0 if out["dtc_registry"]["DTC_0x01"]["status"] == "PENDING" else 0.0, 0.0, 0.0)
    
    # Step 2: PENDING
    out = mut.step(stimulator.stimulus_bus)
    verdict_engine.evaluate("OV_PENDING_2", 1.0, 1.0 if out["dtc_registry"]["DTC_0x01"]["status"] == "PENDING" else 0.0, 0.0, 0.0)
    
    # Step 3: CONFIRMED
    out = mut.step(stimulator.stimulus_bus)
    verdict_engine.evaluate("OV_CONFIRMED", 1.0, 1.0 if out["dtc_registry"]["DTC_0x01"]["status"] == "CONFIRMED" else 0.0, 0.0, 0.0)

    return {
        "verdict": verdict_engine.get_overall_verdict(),
        "details": "Verified OV diagnostic escalation PENDING -> CONFIRMED (3 steps).",
        "signals_in": ["cell_voltages"],
        "signals_out": ["dtc_registry"]
    }
