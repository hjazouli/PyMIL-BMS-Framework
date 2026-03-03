"""
mut/bms_model.py — Layer 3: Model Under Test (Full-featured BMS)

This module implements a comprehensive BMS algorithm including cell monitoring,
diagnostics, thermal management, state estimation (SOC/SOH/SOP/SOE), and safety logic.
It is organized into 12 functional blocks orchestrated by the step() method.

MUT Interface Contract:
    step(inputs: dict) -> dict
"""

import logging
import statistics
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants & Lookups
# ---------------------------------------------------------------------------
_OCV_TABLE = [
    (0.0,   3.00), (5.0,   3.20), (10.0,  3.35), (20.0,  3.55),
    (30.0,  3.67), (40.0,  3.73), (50.0,  3.79), (60.0,  3.84),
    (70.0,  3.89), (80.0,  3.92), (90.0,  3.96), (95.0,  4.04),
    (100.0, 4.18),
]

_TEMP_SOC_CORRECTION = [
    (-20, 0.85), (-10, 0.90), (0, 0.95), (25, 1.00), (45, 1.02), (60, 1.05)
]

def _interpolate(table: List[tuple], x: float) -> float:
    if x <= table[0][0]: return table[0][1]
    if x >= table[-1][0]: return table[-1][1]
    for i in range(len(table)-1):
        x0, y0 = table[i]
        x1, y1 = table[i+1]
        if x0 <= x <= x1:
            return y0 + (x - x0) * (y1 - y0) / (x1 - x0)
    return table[-1][1]

# ---------------------------------------------------------------------------
# BMSModel Class
# ---------------------------------------------------------------------------

class BMSModel:
    NOMINAL_CAPACITY_AH: float = 100.0
    OCV_CORRECTION_WEIGHT: float = 0.002
    N_CELLS: int = 6

    def __init__(self, initial_soc_pct: float = 95.0, timestep_s: float = 0.1) -> None:
        self.reset(initial_soc_pct, timestep_s)

    def reset(self, initial_soc_pct: float = 95.0, timestep_s: float = 0.1) -> None:
        self._soc_pct = initial_soc_pct
        self._timestep_s = timestep_s
        self._capacity_ah = self.NOMINAL_CAPACITY_AH
        self._step_count = 0
        self._safe_state = False
        self._safe_state_reason = "NONE"
        self._dtc_registry: Dict[str, Dict] = {
            f"DTC_0x0{i:X}": {"status": "INACTIVE", "pending_count": 0, "confirm_count": 0, "freeze_frame": {}}
            for i in range(1, 11)
        }
        self._charge_state = "IDLE"
        self._contactor_state = "OPEN"
        self._precharge_timer = 0
        logger.debug("BMSModel reset: SOC=%.1f%% dt=%.3f", initial_soc_pct, timestep_s)

    def step(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        self._step_count += 1
        
        # 1. Basic Monitoring & Estimation
        mon = self._block_monitoring(inputs)
        est = self._block_soc_soh(inputs)
        hvdc = self._block_hvdc(inputs, est["SOC_estimated"])
        imd = self._block_imd(inputs)
        balancing = self._block_balancing(inputs, est["SOC_estimated"])
        
        # 2. Diagnostics (Depends on 1)
        dtc = self._block_dtc(mon, est, balancing, hvdc, {}, imd, inputs)
        
        # 3. Safety Logic (Depends on 2)
        safe = self._block_safe_state(dtc, imd, inputs)
        
        # 4. Control & Output (Depends on 3: respects self._safe_state)
        thermal = self._block_thermal(inputs)
        sop = self._block_sop(est, thermal, inputs.get("pack_voltage_V", 400.0))
        soe = self._block_soe(est, inputs.get("pack_voltage_V", 400.0))
        charge = self._block_charge_control(inputs, est["SOC_estimated"], thermal["T_max"], sop["SOP_charge_kW"])
        contactor = self._block_contactor(est, inputs, dtc)
        
        # Merge all outputs
        out = {}
        for d in [mon, est, thermal, balancing, sop, soe, hvdc, charge, dtc, contactor, imd, safe]:
            out.update(d)
        return out

    # ---------------------------------------------------------------------------
    # Functional Blocks
    # ---------------------------------------------------------------------------

    def _block_monitoring(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        voltages = inputs.get("cell_voltages", [3.7]*6)
        temps = inputs.get("cell_temperatures", [25.0]*6)
        
        ov_flags = [v > 4.18 for v in voltages]
        uv_flags = [v < 2.80 for v in voltages]
        ot_flags = [t > 55.0 for t in temps]
        ut_flags = [t < -20.0 for t in temps]
        
        severity = []
        for i in range(6):
            if ov_flags[i] or uv_flags[i] or ot_flags[i] or ut_flags[i]:
                severity.append("FAULT")
            elif voltages[i] >= 4.15 or voltages[i] <= 3.10 or temps[i] >= 45.0 or temps[i] <= -10.0:
                severity.append("WARNING")
            else:
                severity.append("NONE")
        
        return {
            "cell_ov_flags": ov_flags, "cell_uv_flags": uv_flags,
            "cell_ot_flags": ot_flags, "cell_ut_flags": ut_flags,
            "cell_fault_severity": severity
        }

    def _block_soc_soh(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        curr = inputs.get("pack_current_A", 0.0)
        volt = inputs.get("pack_voltage_V", 400.0)
        cap = inputs.get("capacity_Ah", self.NOMINAL_CAPACITY_AH)
        temp = statistics.mean(inputs.get("cell_temperatures", [25.0]*6))
        
        # CC
        self._soc_pct += (curr * self._timestep_s / 3600.0) / cap * 100.0
        # OCV sync
        v_cell_avg = volt / self.N_CELLS
        ocv_soc = _interpolate([(v, s) for s, v in _OCV_TABLE], v_cell_avg)
        self._soc_pct = (1-self.OCV_CORRECTION_WEIGHT)*self._soc_pct + self.OCV_CORRECTION_WEIGHT*ocv_soc
        
        self._soc_pct = max(0.0, min(100.0, self._soc_pct))
        
        # Temp correction (SOP/Reporting only)
        temp_factor = _interpolate(_TEMP_SOC_CORRECTION, temp)
        corrected_soc = self._soc_pct * temp_factor
        
        soh = cap / self.NOMINAL_CAPACITY_AH
        
        return {
            "SOC_estimated": round(corrected_soc, 2),
            "SOC_raw": round(self._soc_pct, 4),
            "SOH_estimated": round(soh, 4),
            "capacity_Ah_estimated": cap
        }

    def _block_thermal(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        temps = inputs.get("cell_temperatures", [25.0]*6)
        t_max = max(temps)
        t_avg = statistics.mean(temps)
        
        req = "NONE"
        if t_max > 55 or self._safe_state: req = "EMERGENCY"
        elif t_max > 45: req = "HIGH"
        elif t_max > 35: req = "LOW"
        
        df = 1.0
        if t_max < 0: df = 0.5
        elif t_max < 15: df = 0.75
        elif t_max < 45: df = 1.0
        elif t_max < 55: df = 0.6
        else: df = 0.0
        
        return {"cooling_request": req, "thermal_derating_factor": df, "T_max": t_max, "T_avg": t_avg}

    def _block_balancing(self, inputs: Dict[str, Any], soc: float) -> Dict[str, Any]:
        v = inputs.get("cell_voltages", [3.7]*6)
        curr = inputs.get("pack_current_A", 0.0)
        v_max, v_min = max(v), min(v)
        delta_v = (v_max - v_min) * 1000
        
        permitted = abs(curr) < 0.1 and soc > 20.0
        active_cells = [permitted and (v_max - cell < 0.005) for cell in v]
        
        return {
            "balancing_active_cells": active_cells, "delta_V_mV": round(delta_v, 2),
            "active_balancing_requested": delta_v > 50, "balancing_permitted": permitted
        }

    def _block_sop(self, est: dict, thermal: dict, volt: float) -> Dict[str, Any]:
        p_chg, p_dis = 150.0, 250.0
        soc, soh = est["SOC_estimated"], est["SOH_estimated"]
        df = thermal["thermal_derating_factor"]
        
        # SOC derating
        if soc < 20: p_dis *= (soc / 20.0)
        if soc > 90: p_chg *= (1 - (soc - 90) / 10.0)
        
        p_chg *= soh * df
        p_dis *= soh * df
        
        if self._safe_state:
            p_chg = 0.0
            p_dis = 0.0
        
        return {"SOP_charge_kW": round(p_chg, 2), "SOP_discharge_kW": round(p_dis, 2)}

    def _block_soe(self, est: dict, volt: float) -> Dict[str, Any]:
        energy = est["SOC_raw"]/100 * est["capacity_Ah_estimated"] * volt / 1000.0
        range_km = (energy / 0.180) * est["SOH_estimated"]
        return {"SOE_kWh": round(energy, 2), "estimated_range_km": round(range_km, 2)}

    def _block_hvdc(self, inputs: Dict[str, Any], soc: float) -> Dict[str, Any]:
        v = inputs.get("pack_voltage_V", 400.0)
        curr = inputs.get("pack_current_A", 0.0)
        
        oc = abs(curr) > 200.0
        df = 1.0
        if v > 420: df = 0.0
        elif v > 400: df = 1.0 - (v - 400) / 20.0
        
        max_curr = 200.0 * df
        if v > 400: max_curr -= (v - 400) * 2.0
            
        return {"HVDC_derating_factor": round(df, 3), "HVDC_overcurrent": oc, "max_current_derated_A": max(0, max_curr)}

    def _block_charge_control(self, inputs: Dict[str, Any], soc: float, t_max: float, sop: float) -> Dict[str, Any]:
        requested = inputs.get("charging_requested", False)
        curr = inputs.get("pack_current_A", 0.0)
        volt = inputs.get("pack_voltage_V", 400.0)
        
        if not requested: self._charge_state = "IDLE"
        elif self._charge_state == "IDLE":
            if soc < 99 and t_max < 45: self._charge_state = "CC"
        elif self._charge_state == "CC":
            if volt >= 4.15 * self.N_CELLS: self._charge_state = "CV"
        elif self._charge_state == "CV":
            if curr < 0.05 * self.NOMINAL_CAPACITY_AH: self._charge_state = "COMPLETE"
        
        target_a = 0.0
        if self._charge_state == "CC": target_a = min(50.0, sop * 1000 / volt)
        elif self._charge_state == "CV": target_a = 5.0 # Tapering
            
        return {"charge_state": self._charge_state, "charge_current_target_A": target_a, "charge_voltage_target_V": 4.2 * self.N_CELLS}

    def _block_dtc(self, mon: dict, est: dict, balancing: dict, hvdc: dict, charge: dict, imd: dict, inputs: dict) -> Dict[str, Any]:
        fault_map = {
            "DTC_0x01": any(mon["cell_ov_flags"]),
            "DTC_0x02": any(mon["cell_uv_flags"]),
            "DTC_0x03": any(mon["cell_ot_flags"]),
            "DTC_0x04": any(mon["cell_ut_flags"]),
            "DTC_0x05": est["SOH_estimated"] < 0.85,
            "DTC_0x06": balancing["delta_V_mV"] > 150,
            "DTC_0x07": imd.get("IMD_fault", False),
            "DTC_0x08": False, # Weld handled in Block 10
            "DTC_0x09": hvdc["HVDC_overcurrent"],
            "DTC_0x0A": False # Charge fault logic simplified
        }
        
        active_count = 0
        highest = "NONE"
        for dtc_id, active in fault_map.items():
            reg = self._dtc_registry[dtc_id]
            if active:
                reg["pending_count"] += 1
                if reg["pending_count"] >= 3:
                    if reg["status"] != "CONFIRMED":
                        reg["status"] = "CONFIRMED"
                        reg["freeze_frame"] = {"SOC": est["SOC_estimated"], "T_max": 25.0, "V": inputs.get("pack_voltage_V")}
                    active_count += 1
                    highest = dtc_id
                else: reg["status"] = "PENDING"
            else:
                reg["pending_count"] = 0
                reg["status"] = "INACTIVE"

        return {"dtc_registry": self._dtc_registry, "active_dtc_count": active_count, "highest_severity_dtc": highest}

    def _block_contactor(self, est: dict, inputs: dict, dtc: dict) -> Dict[str, Any]:
        cmd_close = inputs.get("contactor_command", False)
        v_bus = inputs.get("hv_bus_voltage_V", 0.0)
        v_pack = inputs.get("pack_voltage_V", 400.0)
        curr = inputs.get("pack_current_A", 0.0)
        
        # Inhibit
        asil_d = ["DTC_0x01", "DTC_0x02", "DTC_0x03", "DTC_0x07"]
        inhibited = any(self._dtc_registry[d]["status"] == "CONFIRMED" for d in asil_d) or self._safe_state
        
        # State Machine
        if self._safe_state:
            self._contactor_state = "OPEN"
        elif self._contactor_state == "OPEN":
            if cmd_close and not inhibited: self._contactor_state = "PRECHARGE"; self._precharge_timer = 0
        elif self._contactor_state == "PRECHARGE":
            self._precharge_timer += 1
            if abs(v_bus - v_pack) < 20 or self._precharge_timer > 50: self._contactor_state = "CLOSED"
            if not cmd_close or inhibited: self._contactor_state = "OPEN"
        elif self._contactor_state == "CLOSED":
            if not cmd_close or inhibited: self._contactor_state = "OPEN"
            
        # Weld detection
        if self._contactor_state == "OPEN" and abs(curr) > 1.0:
            self._dtc_registry["DTC_0x08"]["status"] = "CONFIRMED"
            
        return {"contactor_state": self._contactor_state, "precharge_complete": self._contactor_state == "CLOSED", "contactor_inhibited": inhibited}

    def _block_imd(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        v = inputs.get("pack_voltage_V", 400.0)
        r_iso = inputs.get("isolation_resistance_ohm", 1e6)
        r_min = 100.0 * v
        
        status = "OK"
        if r_iso <= r_min: status = "FAULT"
        elif r_iso <= r_min * 1.5: status = "WARNING"
        
        return {"isolation_status": status, "R_iso_min_ohm": r_min, "IMD_fault": status == "FAULT"}

    def _block_safe_state(self, dtc: dict, imd: dict, inputs: dict) -> Dict[str, Any]:
        asil_d = ["DTC_0x01", "DTC_0x02", "DTC_0x03", "DTC_0x07"]
        fault_present = any(self._dtc_registry[d]["status"] == "CONFIRMED" for d in asil_d)
        reset_req = inputs.get("reset_requested", False)
        
        if fault_present:
            if not self._safe_state:
                self._safe_state = True
                self._safe_state_reason = dtc["highest_severity_dtc"]
        elif reset_req:
            # Recovery: all ASIL-D DTCs must be INACTIVE
            if not any(self._dtc_registry[d]["status"] != "INACTIVE" for d in asil_d):
                self._safe_state = False
                self._safe_state_reason = "NONE"
        
        return {
            "SAFE_STATE": self._safe_state, 
            "safe_state_reason": self._safe_state_reason, 
            "fault_tolerance_steps": 3
        }
