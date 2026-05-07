from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from math import ceil
from typing import Deque


@dataclass
class PitxWaitPrediction:
    people_count: int
    people_smoothed: int
    estimated_wait_minutes: int
    service_level: str
    queue_note: str
    confidence: int


class PitxWaitTimeForecaster:
    """Explainable wait-time forecasting for a one-day hackathon demo.

    It intentionally avoids a black-box model so judges can understand the
    logic: count people, smooth the count, estimate how many dispatch cycles are
    needed, then turn that into minutes.
    """

    def __init__(self) -> None:
        self._recent_counts: Deque[int] = deque(maxlen=12)
        self.bus_capacity = 45
        self.dispatch_headway_min = 6
        self.boarding_rate_per_min = 9
        self.base_terminal_delay_min = 3

    def _smoothed_count(self, current: int) -> int:
        self._recent_counts.append(max(0, int(current)))
        values = sorted(self._recent_counts)
        if len(values) >= 6:
            values = values[1:-1]
        return int(round(sum(values) / max(len(values), 1)))

    @staticmethod
    def _level(wait: int) -> str:
        if wait >= 25:
            return "Heavy"
        if wait >= 16:
            return "Moderate"
        return "Light"

    @staticmethod
    def _note(level: str) -> str:
        if level == "Heavy":
            return "Long queue. Suggest alternatives before commuters commit to the line."
        if level == "Moderate":
            return "Queue is building. Give commuters a clear wait estimate."
        return "Queue is manageable. Current route remains practical."

    def predict(self, current_people_count: int) -> PitxWaitPrediction:
        raw_count = max(0, int(current_people_count))
        people = self._smoothed_count(raw_count)

        cycles_needed = max(1, ceil(people / max(self.bus_capacity, 1)))
        dispatch_delay = (cycles_needed - 1) * self.dispatch_headway_min
        boarding_time = min(
            self.dispatch_headway_min,
            int(round(people / max(self.boarding_rate_per_min, 1))),
        )
        wait = self.base_terminal_delay_min + dispatch_delay + boarding_time
        wait = max(4, min(60, int(wait)))
        level = self._level(wait)

        confidence = 91
        if raw_count == 0:
            confidence = 72
        elif abs(raw_count - people) > 12:
            confidence = 84

        return PitxWaitPrediction(
            people_count=raw_count,
            people_smoothed=people,
            estimated_wait_minutes=wait,
            service_level=level,
            queue_note=self._note(level),
            confidence=confidence,
        )


pitx_forecaster = PitxWaitTimeForecaster()
