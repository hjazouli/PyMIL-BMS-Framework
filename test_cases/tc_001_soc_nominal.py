"""
test_cases/tc_001_soc_nominal.py — Layer 2
ASPICE Level: SYS.4 Base Estimation
"""
import logging
import os
from typing import Any, Dict

logger = logging.getLogger(__name__)

def run(stimulator, measurement, verdict_engine) -> Dict[str, Any]:
    stimulator.reset()
    measurement.clear()
    verdict_engine.clear_history()

    mut = stimulator.model
    if not mut: raise RuntimeError("No MUT")
    mut.reset(initial_soc_pct=95.0, timestep_s=60.0)

    _here = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(_here, "..", "stimuli", "wltp_discharge.csv")

    with open(csv_path, newline="", encoding="utf-8") as fh:
        import csv
        reader = csv.DictReader(fh)
        for i, row in enumerate(reader):
            curr = float(row["current_A"])
            volt = float(row["voltage_V"])
            target_soc = float(row["SOC_reference"])
            
            stimulator.send("pack_current_A", curr)
            stimulator.send("pack_voltage_V", volt)
            stimulator.send("cell_voltages", [volt/6]*6)
            stimulator.send("cell_temperatures", [float(row["temperature_C"])]*6)
            
            outputs = mut.step(stimulator.stimulus_bus)
            soc = outputs["SOC_estimated"]
            
            measurement.record("SOC_estimated", soc, i*60.0)
            verdict_engine.evaluate(f"SOC_Step_{i}", target_soc, soc, 5.0, 7.0)

    final_soc = measurement.get_latest("SOC_estimated")
    return {
        "verdict": verdict_engine.get_overall_verdict(),
        "details": f"WLTP tracking complete. Final SOC: {final_soc:.2f}%.",
        "signals_in": ["pack_current_A", "pack_voltage_V"],
        "signals_out": ["SOC_estimated"]
    }
