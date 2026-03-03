import sys
import os
import time
import logging
import yaml

# Add root to path for framework imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from framework.hil.realtime_scheduler import RealtimeScheduler
from plant.plant_can_interface import PlantCANInterface

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s — %(message)s')
logger = logging.getLogger("PlantSimulator")

class PlantSimulator:
    """
    Real-time battery plant model (Subprocess).
    """

    def __init__(self, config_path="plant/plant_config.yaml"):
        # Initial State
        self.state = {
            "cells": [3.7, 3.7, 3.7, 3.7],
            "soc": 60.0,
            "soh": 95.0,
            "current": 0.0,
            "temp": 25.0
        }
        self.can = PlantCANInterface()
        self.scheduler = RealtimeScheduler(tick_ms=100)

    def step(self):
        """One pulse of the plant models."""
        # 1. Read Commands (e.g. from MUT)
        cmds = self.can.read_inputs()
        
        # 2. Update Model Physics (Simplified)
        # Current follows requested stimulus usually, but plant can react to MUT commands
        # For this HIL demo, we'll assume current is injected by the test case via CAN or global
        
        # Simple SOC tracking in plant
        # SOC_new = SOC - (I * dt / Cap)
        dt = 0.1 # 100ms
        capacity_ah = 100.0
        self.state["soc"] -= (self.state["current"] * dt / (capacity_ah * 3600.0)) * 100.0
        
        # Voltage follows SOC
        # V = OCV(SOC) - I*R
        v_ocv = 3.3 + (self.state["soc"] / 100.0) * 0.9
        for i in range(4):
            self.state["cells"][i] = v_ocv - (self.state["current"] * 0.01)

        # 3. Publish State
        self.can.publish_state(self.state)

    def run(self):
        logger.info("Plant Simulator thread running at 100ms...")
        try:
            while True:
                self.scheduler.run(self.step, duration_s=1.0) # Run in slices
        except KeyboardInterrupt:
            logger.info("Plant Simulator shutting down.")

if __name__ == "__main__":
    plant = PlantSimulator()
    plant.run()
