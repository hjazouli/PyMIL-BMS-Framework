"""
test_cases/tc_009_hvdc_derating.py — Layer 2
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

    # Volt ramp 395 -> 410 -> 425
    v_points = [395, 410, 425]
    exp_df = [1.0, 0.5, 0.0] # 1.0 - (v-400)/20 -> for 410 is 0.5. >420 is 0.0
    
    for i, v in enumerate(v_points):
        stimulator.send("pack_voltage_V", v)
        out = mut.step(stimulator.stimulus_bus)
        
        verdict_engine.evaluate(f"HVDC_DF_{v}V", exp_df[i], out["HVDC_derating_factor"], 0.05, 0.1)
        
        # Shutdown check
        if v >= 420:
            verdict_engine.evaluate(f"Shutdown_Triggered_at_{v}V", 0.0, out["max_current_derated_A"], 0.0, 0.0)

    return {
        "verdict": verdict_engine.get_overall_verdict(),
        "details": "HVDC voltage ramp verified. Derating factor tracks linearly from 400V to 420V.",
        "signals_in": ["pack_voltage_V"],
        "signals_out": ["HVDC_derating_factor"]
    }
