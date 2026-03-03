import time
import logging
from typing import Callable

logger = logging.getLogger(__name__)

class RealtimeScheduler:
    """
    Hard 100ms tick enforcement for HIL simulations.
    """

    def __init__(self, tick_ms: int = 100) -> None:
        self.tick_s = tick_ms / 1000.0
        self._timing_violations = 0
        self._deltas = []

    def run(self, action: Callable, duration_s: float) -> None:
        """
        Executes 'action' every tick_s for duration_s.
        """
        start_time = time.perf_counter()
        next_tick = start_time
        end_time = start_time + duration_s
        
        logger.info("Scheduler started | tick=%dms | duration=%ds", int(self.tick_s*1000), duration_s)

        while time.perf_counter() < end_time:
            tick_start = time.perf_counter()
            
            # Execute the HIL step
            try:
                action()
            except Exception as e:
                logger.error("Scheduler action failed: %s", e)

            # High-precision wait for next tick
            next_tick += self.tick_s
            wait_time = next_tick - time.perf_counter()
            
            if wait_time > 0:
                time.sleep(wait_time)
            else:
                # We missed a deadline
                drift = abs(wait_time)
                if drift > (self.tick_s * 0.1):
                    self._timing_violations += 1
                    logger.warning("[TIMING_VIOLATION] Drift=%.2fms", drift * 1000)
            
            self._deltas.append(time.perf_counter() - tick_start)

    def get_report(self) -> dict:
        if not self._deltas: return {}
        return {
            "avg_tick_ms": (sum(self._deltas)/len(self._deltas)) * 1000.0,
            "max_tick_ms": max(self._deltas) * 1000.0,
            "violations": self._timing_violations
        }
