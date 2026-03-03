"""
test_cases/tc_002_soc_stress.py — Layer 2
ASPICE Level: SYS.5 Robustness
"""
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

def run(stimulator, measurement, verdict_engine) -> Dict[str, Any]:
    stimulator.reset()
    measurement.clear()
    verdict_engine.clear_history()

    mut = stimulator.model
    mut.reset(initial_soc_pct=80.0, timestep_s=1.0)

    for i in range(100):
        curr = -150.0 if (i % 20 < 10) else 0.0
        stimulator.send("pack_current_A", curr)
        stimulator.send("pack_voltage_V", 380.0 if curr < 0 else 400.0)
        stimulator.send("cell_voltages", [3.8/6 if curr < 0 else 4.0/6]*6)
        
        outputs = mut.step(stimulator.stimulus_bus)
        soc = outputs["SOC_estimated"]
        measurement.record("SOC_estimated", soc, float(i))
        
        if soc < 0.0 or soc > 100.0:
            verdict_engine.evaluate("SOC_Boundary", 50.0, soc, 50.0, 50.0)

    return {
        "verdict": verdict_engine.get_overall_verdict(),
        "details": "Pulse discharge stress test complete.",
        "signals_in": ["pack_current_A"],
        "signals_out": ["SOC_estimated"]
    }
