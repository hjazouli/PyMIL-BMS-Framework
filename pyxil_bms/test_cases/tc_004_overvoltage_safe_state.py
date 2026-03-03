"""
test_cases/tc_004_overvoltage_safe_state.py — Layer 2

TC_004: Over-voltage & Safe State Diagnostics
=============================================
Objective:
    Verify the 3-step latching logic for SAFE_STATE.
    SAFE_STATE must become True (1.0) only after DTC_OV has been True
    for 3 consecutive steps of simulation.

Acceptance criteria:
    Step 1: Voltage=4.2V -> DTC_OV=1, SAFE_STATE=0
    Step 2: Voltage=4.2V -> DTC_OV=1, SAFE_STATE=0
    Step 3: Voltage=4.2V -> DTC_OV=1, SAFE_STATE=1
    Step 4: Voltage=3.7V -> DTC_OV=0, SAFE_STATE=1 (Latched)

Framework API used:
    stimulator.send()
    measurement.record()
    verdict_engine.evaluate()
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

def run(stimulator, measurement, verdict_engine) -> Dict[str, Any]:
    stimulator.reset()
    measurement.clear()
    verdict_engine.clear_history()

    mut = stimulator.model
    if mut is None:
        raise RuntimeError("No MUT model injected.")

    # Normal starting point
    mut.reset(initial_soc_pct=50.0, timestep_s=1.0)

    steps_data = [
        {"v": 4.20, "exp_ov": 1.0, "exp_safe": 0.0}, # Step 1: OV active
        {"v": 4.21, "exp_ov": 1.0, "exp_safe": 0.0}, # Step 2: OV active
        {"v": 4.22, "exp_ov": 1.0, "exp_safe": 1.0}, # Step 3: SAFE_STATE triggers
        {"v": 3.70, "exp_ov": 0.0, "exp_safe": 1.0}, # Step 4: Latch check
    ]

    worst = "PASS"

    for i, step in enumerate(steps_data):
        t = float(i)
        stimulator.send("voltage_V", step["v"])
        stimulator.send("current_A", 0.0)
        
        outputs = mut.step(stimulator.stimulus_bus)
        
        ov = outputs["DTC_OV"]
        safe = outputs["SAFE_STATE"]
        
        measurement.record("DTC_OV", ov, t)
        measurement.record("SAFE_STATE", safe, t)

        v_ov = verdict_engine.evaluate(f"DTC_OV_Step_{i+1}", step["exp_ov"], ov, 0.0, 0.0)
        v_safe = verdict_engine.evaluate(f"SAFE_STATE_Step_{i+1}", step["exp_safe"], safe, 0.0, 0.0)
        
        if v_ov == "FAIL" or v_safe == "FAIL":
            worst = "FAIL"

    details = f"Verified 3-step OV diagnostic. Safe state latched at step 3 and remained at step 4."
    return {
        "verdict": worst,
        "details": details,
        "signals_in": ["voltage_V"],
        "signals_out": ["DTC_OV", "SAFE_STATE"],
    }
