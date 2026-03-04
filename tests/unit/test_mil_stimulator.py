import os
import pytest
from framework.mil.mil_stimulator import MILStimulator

def test_mil_stimulator_send():
    stim = MILStimulator()
    stim.send("test_sig", 42.0)
    assert stim.get_stimulus_bus()["test_sig"] == 42.0

def test_mil_stimulator_reset():
    stim = MILStimulator()
    stim.send("test_sig", 42.0)
    stim.reset()
    assert len(stim.get_stimulus_bus()) == 0

def test_mil_stimulator_send_profile(tmp_path):
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("time,val\n0,1.0\n1,2.0")
    
    stim = MILStimulator()
    stim.send_profile("profile_sig", str(csv_file), "val")
    assert stim.get_stimulus_bus()["profile_sig"] == 2.0
