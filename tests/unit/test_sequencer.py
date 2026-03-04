from framework.sequencer import Sequencer

def test_dependency_resolution():
    seq = Sequencer()
    results = {
        "TC_001": {"verdict": "PASS"},
        "TC_002": {"verdict": "FAIL"}
    }
    
    # Test with depends_on: null always runs
    assert seq._resolve_dependencies(results, {"id": "TC_003"}) is True
    
    # Test with depends_on: TC_001 runs normally when TC_001 returns PASS
    assert seq._resolve_dependencies(results, {"id": "TC_004", "depends_on": "TC_001"}) is True
    
    # Test with depends_on: TC_002 is BLOCKED when TC_002 returns FAIL
    assert seq._resolve_dependencies(results, {"id": "TC_005", "depends_on": "TC_002"}) is False
