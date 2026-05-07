from __future__ import annotations

from typing import Dict
from forecasting_ai import PitxWaitPrediction


def build_route_suggestion(prediction: PitxWaitPrediction, people_count: int) -> Dict[str, object]:
    wait = prediction.estimated_wait_minutes

    if wait < 16:
        return {
            "is_optimal": True,
            "title": "Stay with PITX for now",
            "message": "The current wait is still manageable. No route change is needed yet.",
            "time_saved_minutes": 0,
            "impact": "Commuter guidance",
        }

    if wait < 25:
        saved = max(5, wait - 12)
        return {
            "is_optimal": False,
            "title": "Consider the EDSA Carousel transfer",
            "message": "Queue is building at PITX Gate 3. Commuters near Roxas Boulevard may save time by using the EDSA Carousel and transferring at Taft Avenue.",
            "time_saved_minutes": saved,
            "impact": "Alternative route",
            "context": {
                "pitx_wait_minutes": wait,
                "visible_people": people_count,
                "assumed_alternative_wait_minutes": wait - saved,
            },
        }

    saved = max(10, wait - 14)
    return {
        "is_optimal": False,
        "title": "Warn commuters before they join the line",
        "message": "Heavy crowding is detected. Recommend nearby transfer options, add staff at the gate, and display the wait time at the entrance.",
        "time_saved_minutes": saved,
        "impact": "Crowd response",
        "context": {
            "pitx_wait_minutes": wait,
            "visible_people": people_count,
            "assumed_alternative_wait_minutes": wait - saved,
        },
    }
