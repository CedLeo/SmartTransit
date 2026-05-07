# Smart Transit Hub: Real-Time Commuter Forecasting

Smart Transit Hub is a one-day hackathon prototype that helps Filipino commuters avoid blind waiting at public transport terminals.

The live demo focuses on **PITX Gate 3 during rush hour**. The system reads a terminal camera feed, counts visible commuters, estimates the current waiting time, and recommends the next best action for commuters and terminal staff.

## Problem

Public transport congestion makes opportunity inequality worse. A student can miss class, a worker can lose paid time, and a family can lose hours simply because they had no clear view of how long a terminal queue would take.

## Solution

Smart Transit Hub gives commuters and terminal teams three simple answers:

1. **How many people are visibly waiting?**
2. **How long might the wait be?**
3. **What should people do next?**

The prototype supports SDGs 4, 8, 10, and 11 by improving access to education, protecting work hours, reducing mobility inequality, and helping cities manage transport spaces better.

## Demo Features

- PITX commuter page with live video stream
- Anonymous person counting from the video feed
- Explainable wait-time estimate
- Route or terminal action recommendation
- Operations dashboard for terminal staff and LGU-style decision makers
- Fallback demo mode when the sample video or YOLO model is not yet available

## Tech Stack

- Frontend: HTML, JavaScript, Tailwind CSS CDN
- Backend: Python Flask
- Video processing: OpenCV
- Person detection: Ultralytics YOLOv11 Nano when `yolo11n.pt` is available
- Forecasting: lightweight explainable queue model

## Folder Structure

```txt
smart_transit_hub/
├── app.py
├── forecasting_ai.py
├── people_counter.py
├── route_ai.py
├── requirements.txt
├── yolo11n.pt                 # optional, place here
├── data/
│   └── pitx_rush_hour.mp4      # optional, place here
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── commuter.html
│   └── lgu_dashboard.html
└── static/
    ├── css/style.css
    └── js/
        ├── home.js
        ├── commuter.js
        └── dashboard.js
```

## How to Run

```bash
python -m venv .venv
.venv\Scripts\activate     # Windows
pip install -r requirements.txt
python app.py
```

Open:

- `http://127.0.0.1:5001/`
- `http://127.0.0.1:5001/commuter`
- `http://127.0.0.1:5001/dashboard`

## Important Demo Note

If `data/pitx_rush_hour.mp4` or `yolo11n.pt` is missing, the app still runs using a visual fallback feed. This prevents the pitch from failing during setup.

## Privacy Promise

The prototype only uses anonymous counts. It does not save videos, faces, names, or personal identities.
