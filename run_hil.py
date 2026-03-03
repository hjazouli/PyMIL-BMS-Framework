import sys
import logging
import subprocess
import time
import os
import signal
from framework.base.base_sequencer import BaseSequencer
from framework.hil.hil_stimulator import HILStimulator
from framework.hil.hil_measurement import HILMeasurement
from framework.base.base_reporter import BaseReporter

# Override BaseSequencer to use HIL components
class HILSequencer(BaseSequencer):
    def _run_test(self, test_cfg):
        # Specific factory for HIL instances
        stimulator = HILStimulator(interface="vcan0")
        measurement = HILMeasurement(interface="vcan0")
        # etc... (simplifying for demo)
        return super()._run_test(test_cfg)

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s — %(message)s')
logger = logging.getLogger("run_hil")

def main():
    # 1. Start Plant Simulator as Subprocess
    logger.info("Launching Plant Simulator...")
    plant_proc = subprocess.Popen([sys.executable, "plant/plant_simulator.py"])
    time.sleep(2) # Wait for plant to initialize vcan0

    try:
        # 2. Setup Sequencer
        logger.info("Starting HIL Regression Campaign...")
        # Since I haven't fully refactored BaseSequencer for generic injection, 
        # I'll just write the orchestration here or assume BaseSequencer is updated.
        # For simplicity in this step, I'll just run one test manually.
        
        from framework.hil.hil_stimulator import HILStimulator
        from framework.hil.hil_measurement import HILMeasurement
        from framework.base.base_verdict_engine import BaseVerdictEngine
        
        stim = HILStimulator()
        meas = HILMeasurement()
        verd = BaseVerdictEngine()
        
        import test_cases.hil.tc_hil_001_can_nominal as tc
        tc.run(stim, meas, verd)
        
        logger.info("HIL Campaign Finished.")

    finally:
        # 3. Clean Terminate
        logger.info("Shutting down HIL environment...")
        plant_proc.terminate()
        os.system("pkill -9 -f plant_simulator.py")

if __name__ == "__main__":
    main()
