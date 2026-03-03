"""
test_cases/tc_007_passive_balancing.py — Layer 2
ASPICE Level: SYS.4 Balancing
"""
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

def run(stimulator, measurement, verdict_engine) -> Dict[str, Any]:
    stimulator.reset()
    measurement.clear()
    verdict_engine.clear_history()

    mut = stimulator.model
    # Must be at rest and SOC > 20%
    mut.reset(initial_soc_pct=50.0, timestep_s=1.0)

    # Imbalance: Cell 0 is highest
    # V_max = 3.82, V_min = 3.80, Delta = 20mV
    stimulator.send("cell_voltages", [3.82, 3.81, 3.80, 3.80, 3.80, 3.80])
    stimulator.send("pack_current_A", 0.0) # Rest
    
    out = mut.step(stimulator.stimulus_bus)
    
    verdict_engine.evaluate("Balancing_Permitted", 1.0, 1.0 if out["balancing_permitted"] else 0.0, 0.0, 0.0)
    verdict_engine.evaluate("Delta_V_mV", 20.0, out["delta_V_mV"], 1.0, 2.0)
    
    # Cell 0 should be active (True)
    # Block 4 logic: active_cells = [permitted and (v_max - cell < 0.005) for cell in v]
    # For Cell 0: 3.82 - 3.82 = 0 < 0.005 -> True
    # For Cell 1: 3.82 - 3.81 = 0.01 > 0.005 -> False
    verdict_engine.evaluate("Cell_0_Balancing", 1.0, 1.0 if out["balancing_active_cells"][0] else 0.0, 0.0, 0.0)
    verdict_engine.evaluate("Cell_2_Not_Balancing", 0.0, 1.0 if out["balancing_active_cells"][2] else 0.0, 0.0, 0.0)

    return {
        "verdict": verdict_engine.get_overall_verdict(),
        "details": f"Passive balancing verified. Delta V: {out['delta_V_mV']}mV. Balancing cells: {out['balancing_active_cells']}",
        "signals_in": ["cell_voltages", "pack_current_A"],
        "signals_out": ["balancing_active_cells"]
    }
