# Pitch and Q&A Notes

## Strong Pitch Angle

Do not pitch this as a generic transport dashboard. Pitch it as a **time-saving commuter decision system**.

Recommended one-liner:

> Smart Transit Hub helps commuters know the wait before they join the line, while helping terminal staff respond before queues become unmanageable.

## What Judges May Ask

### 1. Is this really solving opportunity inequality?

Answer:

Yes, because transport waiting time directly affects access to school, work, and essential services. The project does not remove poverty by itself, but it reduces one daily barrier that affects low-income commuters more than private car users.

### 2. Why focus only on PITX?

Answer:

For a one-day hackathon, we chose one concrete terminal so the demo is complete and believable. PITX is a strong pilot because it is a major transfer point. The same method can later be applied to other terminals.

### 3. Is the wait-time estimate accurate?

Answer:

For the prototype, it is an explainable estimate based on visible queue count, bus capacity, boarding rate, and dispatch interval. For real deployment, the model should be improved using historical queue data, dispatch logs, and ground-truth waiting times.

### 4. What about privacy?

Answer:

The system only needs anonymous person counts. It does not need names, faces, identity matching, or video storage. In a real setup, processing can happen locally at the terminal and only the count can be sent to the dashboard.

### 5. What if the camera angle is bad?

Answer:

Camera placement matters. The demo assumes a fixed view of the queue area. In deployment, each terminal gate needs calibration, testing, and signage that clearly states anonymous counting is being used.

### 6. Why not just use Google Maps or Waze?

Answer:

Navigation apps show road traffic. They usually do not show the actual queue inside a terminal gate. Our value is terminal-level visibility: how crowded the boarding area is and whether a commuter should wait, transfer, or choose a different time.

### 7. What is the biggest limitation?

Answer:

The prototype depends on sample video and assumptions. It proves the workflow, not a city-wide deployment. The next step is collecting real PITX wait-time labels and comparing predictions against actual commuter waiting times.

## Terms to Avoid During Pitch

Avoid saying:

- IoT
- Smart city buzzwords without explaining them
- Fully accurate
- Solves all traffic
- Nationwide-ready now

Use instead:

- Camera-based queue counting
- Wait-time estimate
- Commuter recommendation
- Terminal response dashboard
- PITX pilot demo
