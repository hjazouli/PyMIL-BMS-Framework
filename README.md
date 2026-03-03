# PyMIL & PyHIL: Modular BMS Validation Framework

![CI](https://github.com/hjazouli/robot-selenium-telematics-e2e/actions/workflows/robot-tests.yml/badge.svg)

Professional Python-based Model-in-the-Loop (MIL) and Hardware-in-the-Loop (HIL) automation for automotive software validation.

## 1. Quick Start

### MIL Mode (Pure Python)

```bash
python3 run_mil.py
```

### HIL Mode (CAN Simulation)

1. **Setup vcan0 (Linux)**
   ```bash
   sudo modprobe vcan
   sudo ip link add dev vcan0 type vcan
   sudo ip link set up vcan0
   ```
2. **Run HIL Campaign**
   ```bash
   python3 run_hil.py
   ```

## 2. Architecture Focus

- **MIL**: High-speed algorithmic verification.
- **HIL**: Real-time protocol, timing, and hardware-fault verification using `python-can` and a hard-realtime scheduler.

## 3. Test Dependencies

Refer to `docs/architecture.md` for a deep dive into the dual-mode data flow.
