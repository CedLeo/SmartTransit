from __future__ import annotations

from datetime import datetime
from pathlib import Path
from flask import Flask, Response, jsonify, render_template

from forecasting_ai import pitx_forecaster
from people_counter import pitx_processor, espana_processor
from route_ai import build_route_suggestion

BASE_DIR = Path(__file__).resolve().parent

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static"),
)

TERMINALS = {
    "pitx": {
        "processor": pitx_processor,
        "name": "PITX Gate 3",
        "area": "Parañaque Integrated Terminal Exchange",
    },
    "espana": {
        "processor": espana_processor,
        "name": "España Jeepney Terminal",
        "area": "España Boulevard",
    },
}

@app.route("/api/terminal/<terminal_id>")
def terminal_status(terminal_id):
    terminal = TERMINALS.get(terminal_id)

    if not terminal:
        return jsonify({"error": "Terminal not found"}), 404

    processor = terminal["processor"]
    status = processor.last_status

    prediction = pitx_forecaster.predict(status.people_count)
    suggestion = build_route_suggestion(prediction, status.people_count)

    return jsonify(
        {
            "terminal": {
                "id": terminal_id,
                "name": terminal["name"],
                "area": terminal["area"],
            },
            "live": {
                "timestamp_iso": status.timestamp_iso,
                "people_count": status.people_count,
                "inference_ms": status.inference_ms,
                "source": status.source,
            },
            "prediction": {
                "estimated_wait_minutes": prediction.estimated_wait_minutes,
                "service_level": prediction.service_level,
                "queue_note": prediction.queue_note,
                "confidence": prediction.confidence,
                "people_smoothed": prediction.people_smoothed,
            },
            "route_suggestion": suggestion,
        }
    )


@app.route("/video_feed/<terminal_id>")
def terminal_feed(terminal_id):
    terminal = TERMINALS.get(terminal_id)

    if not terminal:
        return "Terminal not found", 404

    return Response(
        terminal["processor"].mjpeg_stream(fps_cap=10.0),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/commuter")
def commuter():
    return render_template("commuter.html")

@app.route("/espana")
def espana():
    return render_template("espana.html")


@app.route("/dashboard")
def dashboard():
    return render_template("lgu_dashboard.html")


@app.route("/video_feed")
def video_feed():
    return Response(
        pitx_processor.mjpeg_stream(fps_cap=10.0),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )

@app.route("/espana_feed")
def espana_feed():
    return Response(
        espana_processor.mjpeg_stream(fps_cap=10.0),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


@app.route("/api/pitx-status")
def api_pitx_status():
    status = pitx_processor.last_status
    prediction = pitx_forecaster.predict(status.people_count)
    suggestion = build_route_suggestion(prediction, status.people_count)



    return jsonify(
        {
            "terminal": {
                "id": "PITX",
                "name": "Parañaque Integrated Terminal Exchange",
                "area": "Gate 3 - EDSA Carousel Bay",
                "demo_scope": "Rush hour commuter queue",
            },
            "live": {
                "timestamp_iso": status.timestamp_iso,
                "timestamp_label": datetime.fromisoformat(status.timestamp_iso).strftime("%b %d, %I:%M:%S %p"),
                "people_count": status.people_count,
                "inference_ms": status.inference_ms,
                "source": status.source,
            },
            "prediction": {
                "estimated_wait_minutes": prediction.estimated_wait_minutes,
                "service_level": prediction.service_level,
                "queue_note": prediction.queue_note,
                "confidence": prediction.confidence,
                "people_smoothed": prediction.people_smoothed,
            },
            "route_suggestion": suggestion,
        }
    )

@app.route("/api/espana-status")
def api_espana_status():
    status = espana_processor.last_status
    prediction = pitx_forecaster.predict(status.people_count)
    suggestion = build_route_suggestion(prediction, status.people_count)

    return jsonify(
        {
            "terminal": {
                "id": "ESPANA",
                "name": "España Jeepney Terminal",
                "area": "España Boulevard",
                "demo_scope": "Rush hour jeepney queue",
            },
            "live": {
                "timestamp_iso": status.timestamp_iso,
                "people_count": status.people_count,
                "inference_ms": status.inference_ms,
                "source": status.source,
            },
            "prediction": {
                "estimated_wait_minutes": prediction.estimated_wait_minutes,
                "service_level": prediction.service_level,
                "queue_note": prediction.queue_note,
                "confidence": prediction.confidence,
                "people_smoothed": prediction.people_smoothed,
            },
            "route_suggestion": suggestion,
        }
    )

@app.route("/api/dashboard/prototype")
def api_dashboard_prototype():
    status = pitx_processor.last_status
    prediction = pitx_forecaster.predict(status.people_count)
    suggestion = build_route_suggestion(prediction, status.people_count)

    now_label = datetime.now().strftime("%b %d, %I:%M %p")
    wait = prediction.estimated_wait_minutes
    count = prediction.people_smoothed

    return jsonify(
        {
            "meta": {
                "last_updated": now_label,
                "coverage": "PITX demo feed only",
                "privacy": "Only anonymous counts are used. No faces or names are saved.",
            },
            "headline": {
                "terminal_name": "PITX Gate 3",
                "queue_length": count,
                "estimated_wait_minutes": wait,
                "service_level": prediction.service_level,
                "confidence": prediction.confidence,
                "source": status.source,
            },
            "forecast": [
                {"label": "Now", "value": wait},
                {"label": "+15m", "value": min(60, wait + 3)},
                {"label": "+30m", "value": max(4, wait - 2)},
                {"label": "+45m", "value": max(4, wait - 5)},
            ],
            "rush_hour_pattern": [
                {"label": "6:30", "value": max(8, count - 22)},
                {"label": "7:00", "value": max(10, count - 14)},
                {"label": "7:30", "value": max(12, count - 8)},
                {"label": "8:00", "value": count},
                {"label": "8:30", "value": min(120, count + 9)},
            ],
            "recommendations": [
                suggestion,
                {
                    "title": "Open one more loading lane" if wait >= 18 else "Keep current lane setup",
                    "message": "This can reduce visible queue pressure before the next bus dispatch." if wait >= 18 else "Queue is still manageable. Keep monitoring the next 15 minutes.",
                    "impact": "Operations",
                },
                {
                    "title": "Send early warning to commuters",
                    "message": "Show the wait time before commuters enter the terminal queue.",
                    "impact": "Commuter time",
                },
            ],
            "equity_cards": [
                {"sdg": "SDG 4", "title": "Students arrive on time", "copy": "Less blind waiting means fewer missed classes."},
                {"sdg": "SDG 8", "title": "Workers protect paid hours", "copy": "Clear wait estimates help people choose better departure times."},
                {"sdg": "SDG 10", "title": "Fair access to mobility", "copy": "Commuters without private cars get better information."},
                {"sdg": "SDG 11", "title": "Smarter public terminals", "copy": "Crowd data helps terminals respond before queues overflow."},
            ],
        }
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
