import json
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict

class StructuredLogger:
    """
    Shared structured logger for PyXIL-BMS.
    Writes JSON lines to a file and prints summaries to console.
    """

    def __init__(self, log_file: str = "reports/pyxil_bms.log"):
        self.log_file = log_file
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        # Clear existing log file at start of campaign
        with open(self.log_file, "w", encoding="utf-8") as f:
            pass

    def _log(self, event_type: str, **kwargs: Any) -> None:
        timestamp = datetime.now().isoformat()
        entry = {
            "timestamp": timestamp,
            "event_type": event_type,
            **kwargs
        }
        
        # Write JSON line to file
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
            
        # Print human-readable summary to console
        msg = kwargs.get("message", "")
        if not msg and "signal_name" in kwargs:
            msg = f"{kwargs['signal_name']} = {kwargs.get('value')}"
            
        print(f"[{timestamp}] {event_type:15} | {msg}")

    def info(self, event_type: str, **kwargs: Any) -> None:
        self._log(event_type, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        self._log("ERROR", message=message, **kwargs)

# Singleton instance
logger = StructuredLogger()
