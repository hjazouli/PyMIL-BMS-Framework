# PyHIL Architecture: MIL vs HIL

## 1. High-Level Topology

```mermaid
graph TD
    subgraph "PyMIL (Model-in-the-Loop)"
        TestCases_MIL[Test Cases] -->|Direct Call| MUT_MIL[BMS Algorithm]
        MUT_MIL -->|Direct Return| TestCases_MIL
    end

    subgraph "PyHIL (Hardware-in-the-Loop)"
        TestCases_HIL[Test Cases] -->|CAN Bus| CAN[vcan0 / Physical CAN]
        CAN -->|CAN Bus| Plant[Plant Simulator]
        CAN -->|CAN Bus| MUT_HIL[BMS Algorithm Process]
    end
```

## 2. Process Boundaries

- **Framework**: Orchestrates tests, stimulation, and measurement.
- **Plant Simulator**: Independent process simulating battery physics.
- **MUT**: In HIL, this is an independent process (or real ECU) that interacts strictly via CAN.

## 3. Component Interaction

1. **Stimulator**: Encodes test data into CAN frames using `cantools`.
2. **Measurement**: Listens to the bus in a background thread and decodes updates.
3. **Scheduler**: Ensures a fixed 100ms pulse for real-time behavior.
