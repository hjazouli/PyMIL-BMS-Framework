"""
test_cases/tc_006_capacity_sensitivity.py — Layer 2

TC_006: Capacity Sensitivity Verification
=========================================
Objective:
    Verify that SOC integration respects the capacity_Ah input.
    A battery with half the capacity should drop SOC twice as fast for the same current.

Acceptance criteria:
    Ratio of SOC drops (Drop_50Ah / Drop_100Ah) should be 2.0.
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

def run(stimulator, measurement, verdict_engine) -> Dict[str, Any]:
    stimulator.reset()
    measurement.clear()
    verdict_engine.clear_history()

    mut = stimulator.model
    
    # Run 1: 100Ah capacity
    mut.reset(initial_soc_pct=90.0, timestep_s=1.0)
    for t in range(360): # 6 mins
        stimulator.send("current_A", -10.0) # 10A discharge
        stimulator.send("capacity_Ah", 100.0)
        # 3.94V + 0.02V (IR drop compensation) = 3.96V (~90% SOC OCV)
        stimulator.send("voltage_V", 3.94)
        outputs = mut.step(stimulator.stimulus_bus)
    
    drop_100 = 90.0 - outputs["SOC_estimated"] # Expect ~1%

    # Run 2: 50Ah capacity
    mut.reset(initial_soc_pct=90.0, timestep_s=1.0)
    for t in range(360):
        stimulator.send("current_A", -10.0)
        stimulator.send("capacity_Ah", 50.0)
        stimulator.send("voltage_V", 3.94)
        outputs = mut.step(stimulator.stimulus_bus)
    
    drop_50 = 90.0 - outputs["SOC_estimated"] # Expect ~2%

    ratio = drop_50 / drop_100 if drop_100 != 0 else 0
    
    verdict = verdict_engine.evaluate("Capacity_Sensitivity_Ratio", 2.0, ratio, 0.05, 0.1)
    
    details = f"Drop at 100Ah: {drop_100:.2f}%, Drop at 50Ah: {drop_50:.2f}%. Ratio: {ratio:.3f}."
    return {
        "verdict": verdict,
        "details": details,
        "signals_in": ["current_A", "capacity_Ah"],
        "signals_out": ["SOC_estimated"],
    }
