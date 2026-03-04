import os
import json
from framework.shared.logger import logger

def test_logger_json_format(tmp_path):
    log_file = tmp_path / "test.log"
    # Re-initialize logger with temp file
    from framework.shared.logger import StructuredLogger
    test_logger = StructuredLogger(log_file=str(log_file))
    
    test_logger.info("TEST_EVENT", message="Hello", val=123)
    
    with open(log_file, "r") as f:
        line = f.readline()
        data = json.loads(line)
        assert data["event_type"] == "TEST_EVENT"
        assert data["message"] == "Hello"
        assert data["val"] == 123
        assert "timestamp" in data

def test_logger_creation():
    # Verify default log file is created in reports/
    from framework.shared.logger import logger
    assert os.path.exists(os.path.dirname(logger.log_file))
