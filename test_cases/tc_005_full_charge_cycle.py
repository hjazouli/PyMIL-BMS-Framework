"""
test_cases/tc_005_full_charge_cycle.py — Layer 2

TC_005: Full Charge & SOC Clamping
==================================
Objective:
    Verify that SOC is correctly clamped at 100.0% during charging.
    Ensure no "wrap-around" or values > 100.0 occur.

Acceptance criteria:
    Start at 98.0%. Charge until > 100.0% calculated.
    Verify final measurement is exactly 100.0.
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

def run(stimulator, measurement, verdict_engine) -> Dict[str, Any]:
    stimulator.reset()
    measurement.clear()
    verdict_engine.clear_history()

    mut = stimulator.model
    # Charge at 100A for 60 steps (1 min)
    # At 100Ah capacity, 100A for 36s = 1% SOC.
    # From 98% we need ~72s to reach 100%. 120s is plenty.
    mut.reset(initial_soc_pct=98.0, timestep_s=1.0)

    for t in range(120):
        # Provide voltage high enough to compensate IR drop and hit OCV limit (4.18V)
        # 4.4V - (100A * 0.002) = 4.2V -> clamped to 4.18V -> OCV pull to 100%
        stimulator.send("current_A", 100.0)
        stimulator.send("voltage_V", 4.40)
        
        outputs = mut.step(stimulator.stimulus_bus)
        soc = outputs["SOC_estimated"]
        measurement.record("SOC_estimated", soc, float(t))

    final_soc = measurement.get_latest("SOC_estimated")
    all_soc = measurement.get_values("SOC_estimated")
    max_soc = max(all_soc)

    v_final = verdict_engine.evaluate("Final_SOC_Clamped", 100.0, final_soc, 0.01, 0.01)
    v_limit = verdict_engine.evaluate("Max_SOC_Limit", 100.0, max_soc, 0.0, 0.0)

    # Worst of two
    verdict = "PASS" if (v_final == "PASS" and v_limit == "PASS") else "FAIL"
    
    details = f"Charged from 98% to 100%. Max SOC reached: {max_soc:.2f}%. Final SOC: {final_soc:.2f}%."
    return {
        "verdict": verdict,
        "details": details,
        "signals_in": ["current_A"],
        "signals_out": ["SOC_estimated"],
    }
