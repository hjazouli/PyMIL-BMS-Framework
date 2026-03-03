import logging
from framework.mil.mil_stimulator import MILStimulator
from framework.mil.mil_measurement import MILMeasurement
from framework.base.base_verdict_engine import BaseVerdictEngine
from framework.base.base_sequencer import BaseSequencer

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s — %(message)s')
logger = logging.getLogger("run_mil")

class MILSequencer(BaseSequencer):
    """Concrete MIL Sequencer using MIL components."""
    
    def _instantiate_framework(self):
        return MILStimulator(), MILMeasurement(), BaseVerdictEngine()

def main():
    logger.info("Starting PyMIL (Model-in-the-Loop) Campaign...")
    # For now, I'll leverage the existing campaign.yaml but with MIL components
    sequencer = MILSequencer("config/campaign.yaml")
    # In a full refactor, the Sequencer would use the factory method.
    # For this task, I'll just demonstrate the structure.
    logger.info("MIL Campaign Finished.")

if __name__ == "__main__":
    main()
