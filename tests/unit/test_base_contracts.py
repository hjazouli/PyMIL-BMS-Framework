import pytest
from framework.base import BaseStimulator, BaseMeasurement, BaseVerdictEngine, BaseSequencer, BaseReporter
from framework.mil.mil_stimulator import MILStimulator
from framework.mil.mil_measurement import MILMeasurement

def test_base_instantiation_error():
    """Any attempt to instantiate Base* class directly must raise TypeError."""
    with pytest.raises(TypeError):
        BaseStimulator()
    with pytest.raises(TypeError):
        BaseMeasurement()
    with pytest.raises(TypeError):
        BaseVerdictEngine()
    with pytest.raises(TypeError):
        BaseSequencer()
    with pytest.raises(TypeError):
        BaseReporter()

def test_mil_implementations_satisfied():
    """MILStimulator and MILMeasurement satisfy the Base interfaces."""
    stim = MILStimulator()
    meas = MILMeasurement()
    
    assert isinstance(stim, BaseStimulator)
    assert isinstance(meas, BaseMeasurement)
