from __future__ import annotations

import math
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Generator, Optional, Tuple

import cv2
import numpy as np

try:
    from ultralytics import YOLO
except Exception:  # Allows the demo to run even before YOLO is installed.
    YOLO = None  # type: ignore


@dataclass
class PitxStatus:
    timestamp_iso: str
    people_count: int
    inference_ms: int
    source: str


class PitxVideoProcessor:
    def __init__(
        self,
        video_path: str | Path,
        model_path: str | Path,
        resize: Tuple[int, int] = (960, 540),
        conf: float = 0.10,
    ) -> None:
        self.video_path = Path(video_path)
        self.model_path = Path(model_path)
        self.resize = resize
        self.conf = conf
        self._lock = threading.Lock()
        self._cap: Optional[cv2.VideoCapture] = None
        self._model = None
        self._tick = 0
        self.last_status = PitxStatus(
            timestamp_iso=datetime.now().isoformat(),
            people_count=0,
            inference_ms=0,
            source="Starting demo feed",
        )

    def _load_video(self) -> bool:
        if self._cap is not None:
            return self._cap.isOpened()
        if not self.video_path.exists():
            return False
        self._cap = cv2.VideoCapture(str(self.video_path))
        return bool(self._cap and self._cap.isOpened())

    def _load_model(self) -> bool:
        if self._model is not None:
            return True
        if YOLO is None or not self.model_path.exists():
            return False
        self._model = YOLO(str(self.model_path))
        return True

    def _read_video_frame(self) -> Optional[np.ndarray]:
        if not self._load_video():
            return None
        assert self._cap is not None
        ok, frame = self._cap.read()
        if not ok or frame is None:
            self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ok, frame = self._cap.read()
        return frame if ok else None

    def _synthetic_frame(self) -> tuple[np.ndarray, int, str, int]:
        start = time.perf_counter()
        width, height = self.resize
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        frame[:] = (14, 23, 36)

        self._tick += 1
        crowd = 38 + int(18 * math.sin(self._tick / 14)) + (self._tick % 9)
        crowd = max(18, min(86, crowd))

        cv2.putText(frame, "PITX GATE 3 DEMO FEED", (32, 46), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
        cv2.putText(frame, "Fallback mode: add data/pitx_rush_hour.mp4 + yolo11n.pt for real detection", (32, 82), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (185, 198, 216), 1)

        cols = 12
        for i in range(crowd):
            row = i // cols
            col = i % cols
            x = 52 + col * 70 + int(6 * math.sin((self._tick + i) / 5))
            y = 145 + row * 42
            if y > height - 55:
                break
            cv2.circle(frame, (x, y), 11, (61, 184, 164), -1)
            cv2.rectangle(frame, (x - 7, y + 12), (x + 7, y + 33), (252, 211, 77), -1)

        visible = min(crowd, cols * max(1, (height - 190) // 42))
        inference_ms = int((time.perf_counter() - start) * 1000)
        return frame, visible, "Demo simulation", inference_ms

    def _infer_people(self, frame: np.ndarray) -> tuple[np.ndarray, int, str, int]:
        if not self._load_model():
            synthetic, count, source, ms = self._synthetic_frame()
            return synthetic, count, source, ms

        start = time.perf_counter()
        resized = cv2.resize(frame, self.resize)
        results = self._model(resized, classes=[0], conf=self.conf, verbose=False)
        people_count = 0
        annotated = resized.copy()

        for result in results:
            if result.boxes is None:
                continue
            for box in result.boxes:
                x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
                people_count += 1
                cv2.rectangle(annotated, (x1, y1), (x2, y2), (61, 184, 164), 2)
                cv2.putText(annotated, "person", (x1, max(18, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (61, 184, 164), 2)

        inference_ms = int((time.perf_counter() - start) * 1000)
        return annotated, people_count, "PITX sample video", inference_ms

    def next_frame_jpeg(self) -> bytes:
        with self._lock:
            raw_frame = self._read_video_frame()
            if raw_frame is None:
                frame, people_count, source, inference_ms = self._synthetic_frame()
            else:
                frame, people_count, source, inference_ms = self._infer_people(raw_frame)

            overlay = frame.copy()
            cv2.rectangle(overlay, (18, 18), (280, 68), (0, 0, 0), -1)
            frame = cv2.addWeighted(overlay, 0.45, frame, 0.55, 0)
            cv2.putText(frame, f"LIVE COUNT: {people_count}", (34, 52), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.circle(frame, (250, 42), 8, (0, 0, 255), -1)

            self.last_status = PitxStatus(
                timestamp_iso=datetime.now().isoformat(),
                people_count=people_count,
                inference_ms=inference_ms,
                source=source,
            )

            ok, jpeg = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 84])
            if not ok:
                raise RuntimeError("Unable to encode video frame.")
            return jpeg.tobytes()

    def mjpeg_stream(self, fps_cap: float = 10.0) -> Generator[bytes, None, None]:
        min_dt = 1.0 / max(fps_cap, 1.0)
        while True:
            start = time.perf_counter()
            frame = self.next_frame_jpeg()
            yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
            elapsed = time.perf_counter() - start
            if elapsed < min_dt:
                time.sleep(min_dt - elapsed)

class EspanaVideoProcessor:
    def __init__(
        self,
        video_path: str | Path,
        model_path: str | Path,
        resize: Tuple[int, int] = (960, 540),
        conf: float = 0.35,
    ) -> None:
        self.video_path = Path(video_path)
        self.model_path = Path(model_path)
        self.resize = resize
        self.conf = conf
        self._lock = threading.Lock()
        self._cap: Optional[cv2.VideoCapture] = None
        self._model = None
        self._tick = 0
        self.last_status = PitxStatus(
            timestamp_iso=datetime.now().isoformat(),
            people_count=0,
            inference_ms=0,
            source="Starting demo feed",
        )

    def _load_video(self) -> bool:
        if self._cap is not None:
            return self._cap.isOpened()
        if not self.video_path.exists():
            return False
        self._cap = cv2.VideoCapture(str(self.video_path))
        return bool(self._cap and self._cap.isOpened())

    def _load_model(self) -> bool:
        if self._model is not None:
            return True
        if YOLO is None or not self.model_path.exists():
            return False
        self._model = YOLO(str(self.model_path))
        return True

    def _read_video_frame(self) -> Optional[np.ndarray]:
        if not self._load_video():
            return None
        assert self._cap is not None
        ok, frame = self._cap.read()
        if not ok or frame is None:
            self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ok, frame = self._cap.read()
        return frame if ok else None

    def _synthetic_frame(self) -> tuple[np.ndarray, int, str, int]:
        start = time.perf_counter()
        width, height = self.resize
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        frame[:] = (14, 23, 36)

        self._tick += 1
        crowd = 38 + int(18 * math.sin(self._tick / 14)) + (self._tick % 9)
        crowd = max(18, min(86, crowd))

        cv2.putText(frame, "PITX GATE 3 DEMO FEED", (32, 46), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
        cv2.putText(frame, "Fallback mode: add data/pitx_rush_hour.mp4 + yolo11n.pt for real detection", (32, 82), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (185, 198, 216), 1)

        cols = 12
        for i in range(crowd):
            row = i // cols
            col = i % cols
            x = 52 + col * 70 + int(6 * math.sin((self._tick + i) / 5))
            y = 145 + row * 42
            if y > height - 55:
                break
            cv2.circle(frame, (x, y), 11, (61, 184, 164), -1)
            cv2.rectangle(frame, (x - 7, y + 12), (x + 7, y + 33), (252, 211, 77), -1)

        visible = min(crowd, cols * max(1, (height - 190) // 42))
        inference_ms = int((time.perf_counter() - start) * 1000)
        return frame, visible, "Demo simulation", inference_ms

    def _infer_people(self, frame: np.ndarray) -> tuple[np.ndarray, int, str, int]:
        if not self._load_model():
            synthetic, count, source, ms = self._synthetic_frame()
            return synthetic, count, source, ms

        start = time.perf_counter()
        resized = cv2.resize(frame, self.resize)
        results = self._model(resized, classes=[0], conf=self.conf, verbose=False)
        people_count = 0
        annotated = resized.copy()

        for result in results:
            if result.boxes is None:
                continue
            for box in result.boxes:
                x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
                people_count += 1
                cv2.rectangle(annotated, (x1, y1), (x2, y2), (61, 184, 164), 2)
                cv2.putText(annotated, "person", (x1, max(18, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (61, 184, 164), 2)

        inference_ms = int((time.perf_counter() - start) * 1000)
        return annotated, people_count, "PITX sample video", inference_ms

    def next_frame_jpeg(self) -> bytes:
        with self._lock:
            raw_frame = self._read_video_frame()
            if raw_frame is None:
                frame, people_count, source, inference_ms = self._synthetic_frame()
            else:
                frame, people_count, source, inference_ms = self._infer_people(raw_frame)

            overlay = frame.copy()
            cv2.rectangle(overlay, (18, 18), (280, 68), (0, 0, 0), -1)
            frame = cv2.addWeighted(overlay, 0.45, frame, 0.55, 0)
            cv2.putText(frame, f"LIVE COUNT: {people_count}", (34, 52), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.circle(frame, (250, 42), 8, (0, 0, 255), -1)

            self.last_status = PitxStatus(
                timestamp_iso=datetime.now().isoformat(),
                people_count=people_count,
                inference_ms=inference_ms,
                source=source,
            )

            ok, jpeg = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 84])
            if not ok:
                raise RuntimeError("Unable to encode video frame.")
            return jpeg.tobytes()

    def mjpeg_stream(self, fps_cap: float = 10.0) -> Generator[bytes, None, None]:
        min_dt = 1.0 / max(fps_cap, 1.0)
        while True:
            start = time.perf_counter()
            frame = self.next_frame_jpeg()
            yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
            elapsed = time.perf_counter() - start
            if elapsed < min_dt:
                time.sleep(min_dt - elapsed)


BASE_DIR = Path(__file__).resolve().parent
pitx_processor = PitxVideoProcessor(
    video_path=BASE_DIR / "data" / "pitx_rush_hour.mp4",
    model_path=BASE_DIR / "yolo11s.pt",
)

espana_processor = EspanaVideoProcessor(
    video_path=BASE_DIR / "data" / "espana_rush_hour.mp4",
    model_path=BASE_DIR / "yolo11m.pt",
)