"""
test_cases/tc_012_contactor_precharge.py — Layer 2
ASPICE Level: SYS.4 Contactor Control
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

    # 1. Start Open
    stimulator.send("contactor_command", False)
    out = mut.step(stimulator.stimulus_bus)
    verdict_engine.evaluate("State_Initial_OPEN", 1.0, 1.0 if out["contactor_state"] == "OPEN" else 0.0, 0.0, 0.0)

    # 2. Command Close -> Transition to PRECHARGE
    stimulator.send("contactor_command", True)
    stimulator.send("hv_bus_voltage_V", 100.0) # Bus low
    stimulator.send("pack_voltage_V", 400.0)
    out = mut.step(stimulator.stimulus_bus)
    verdict_engine.evaluate("State_PRECHARGE", 1.0, 1.0 if out["contactor_state"] == "PRECHARGE" else 0.0, 0.0, 0.0)

    # 3. Increase Bus Voltage -> CLOSED
    stimulator.send("hv_bus_voltage_V", 390.0) # Delta < 20V
    out = mut.step(stimulator.stimulus_bus)
    verdict_engine.evaluate("State_CLOSED", 1.0, 1.0 if out["contactor_state"] == "CLOSED" else 0.0, 0.0, 0.0)

    # 4. Weld detection check
    # Reset, then OPEN but with current
    mut.reset(initial_soc_pct=50.0, timestep_s=1.0)
    stimulator.send("contactor_command", False)
    stimulator.send("pack_current_A", 10.0) # Flowing while OPEN
    out = mut.step(stimulator.stimulus_bus)
    
    # DTC_0x08 should be CONFIRMED (Weld handled in Block 10)
    reg = out["dtc_registry"]["DTC_0x08"]
    verdict_engine.evaluate("Weld_DTC_Confirmed", 1.0, 1.0 if reg["status"] == "CONFIRMED" else 0.0, 0.0, 0.0)

    return {
        "verdict": verdict_engine.get_overall_verdict(),
        "details": "Contactor logic verified: OPEN -> PRECHARGE -> CLOSED. Weld detection confirmed.",
        "signals_in": ["contactor_command", "hv_bus_voltage_V", "pack_current_A"],
        "signals_out": ["contactor_state", "dtc_registry"]
    }
