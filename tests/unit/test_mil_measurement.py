from framework.mil.mil_measurement import MILMeasurement

def test_mil_measurement_record():
    meas = MILMeasurement()
    meas.record("sig", 10.0, 0.0)
    meas.record("sig", 20.0, 1.0)
    
    assert meas.get_latest("sig") == 20.0
    series = meas.get_series("sig")
    assert len(series) == 2
    assert series[0] == (0.0, 10.0)

def test_mil_measurement_clear():
    meas = MILMeasurement()
    meas.record("sig", 10.0, 0.0)
    meas.clear()
    assert meas.get_latest("sig") == 0.0
    assert len(meas.get_series("sig")) == 0
