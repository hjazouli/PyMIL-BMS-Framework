import pytest
from framework.verdict_engine import VerdictEngine

def test_evaluate_boundaries():
    ve = VerdictEngine()
    # Zone 1: |delta| <= pass_tol -> PASS
    assert ve.evaluate("sig", 100, 105, 5.0, 10.0) == "PASS"
    assert ve.evaluate("sig", 100, 95, 5.0, 10.0) == "PASS"
    
    # Zone 2: pass_tol < |delta| <= warn_tol -> INCONCLUSIVE
    assert ve.evaluate("sig", 100, 106, 5.0, 10.0) == "INCONCLUSIVE"
    assert ve.evaluate("sig", 100, 91, 5.0, 10.0) == "INCONCLUSIVE"
    
    # Zone 3: |delta| > warn_tol -> FAIL
    assert ve.evaluate("sig", 100, 111, 5.0, 10.0) == "FAIL"
    assert ve.evaluate("sig", 100, 89, 5.0, 10.0) == "FAIL"

def test_evaluate_series():
    ve = VerdictEngine()
    exp = [10, 10, 10]
    act = [10, 16, 21] # PASS, INCONCLUSIVE, FAIL
    assert ve.evaluate_series("series", exp, act, 5.0, 10.0) == "FAIL"
    
    ve.clear_history()
    act = [10, 16, 10] # PASS, INCONCLUSIVE, PASS
    assert ve.evaluate_series("series", exp, act, 5.0, 10.0) == "INCONCLUSIVE"

def test_negative_delta():
    ve = VerdictEngine()
    # actual < expected, delta is positive
    assert ve.evaluate("sig", 100, 90, 5.0, 10.0) == "INCONCLUSIVE"
