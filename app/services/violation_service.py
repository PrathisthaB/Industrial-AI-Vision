"""
Violation service — orchestrates the detection engine against a video source
(webcam / uploaded file / CCTV stream) and turns raw per-frame detections into
persisted violation records + evidence screenshots.

A per-camera, per-violation-type cooldown prevents a single ongoing
non-compliance event (e.g. one worker standing without a helmet for 30
seconds) from flooding the database with duplicate rows for every frame.
"""

import time
import threading
from pathlib import Path

import cv2

from app.database import get_db
from app.models import Violation, Session
from app.services.detection_service import (
    DetectionEngine,
    draw_detections,
    is_duplicate_frame,
    compute_worker_compliance,
    severity_for,
    timestamped_filename,
)


class CooldownTracker:
    """Tracks last-logged time per (camera_id, violation_type) to de-duplicate."""

    def __init__(self, cooldown_seconds=8):
        self.cooldown_seconds = cooldown_seconds
        self._last_logged = {}
        self._lock = threading.Lock()

    def should_log(self, camera_id, violation_type):
        key = (camera_id, violation_type)
        now = time.time()
        with self._lock:
            last = self._last_logged.get(key, 0)
            if now - last >= self.cooldown_seconds:
                self._last_logged[key] = now
                return True
            return False


class ViolationPipeline:
    """
    Stateful helper bound to one processing session (one camera / one upload
    job). Call `process_frame` for every frame; it returns the annotated
    frame plus any violations logged this frame.
    """

    def __init__(self, app, camera_id=None, session_id=None):
        self.app = app
        self.camera_id = camera_id
        self.session_id = session_id
        self.engine = DetectionEngine.get_instance(app.config)
        self.cooldown = CooldownTracker(app.config["VIOLATION_COOLDOWN_SECONDS"])
        self.frame_skip = app.config["FRAME_SKIP"]
        self.dup_threshold = app.config["DUPLICATE_FRAME_THRESHOLD"]
        self.violations_dir = Path(app.config["VIOLATIONS_DIR"])
        self.violations_dir.mkdir(parents=True, exist_ok=True)

        self._frame_index = 0
        self._prev_frame = None
        self._last_detections = []
        self._frames_processed = 0
        self._max_workers_seen = 0

    def process_frame(self, frame):
        """
        Returns (annotated_frame, new_violations, workers).
        Applies frame-skip + duplicate-frame elision: on skipped/duplicate
        frames the last known detections are reused (and redrawn) so the
        stream still looks live without re-running inference every frame.
        """
        self._frame_index += 1
        run_inference = (self._frame_index % max(1, self.frame_skip) == 0) and not (
            is_duplicate_frame(self._prev_frame, frame, self.dup_threshold)
        )

        if run_inference:
            detections = self.engine.infer(frame)
            self._last_detections = detections
            self._prev_frame = frame.copy()
            self._frames_processed += 1
        else:
            detections = self._last_detections

        workers = compute_worker_compliance(detections)
        self._max_workers_seen = max(self._max_workers_seen, len(workers))

        new_violations = []
        if run_inference:
            new_violations = self._log_violations(frame, workers)

        annotated = draw_detections(frame.copy(), detections)
        annotated = self._overlay_compliance(annotated, workers)

        if self.session_id and self._frame_index % 15 == 0:
            Session.update_progress(
                self.session_id, self._frames_processed, self._max_workers_seen
            )

        return annotated, new_violations, workers

    def _log_violations(self, frame, workers):
        logged = []
        for worker in workers:
            for item in worker["missing"]:
                violation_type = f"missing_{item}"
                if not self.cooldown.should_log(self.camera_id, violation_type):
                    continue

                screenshot_path = self._save_screenshot(frame, worker, violation_type)
                severity = severity_for(worker["missing"])
                confidence = round(1 - (worker["compliance_score"] / 100), 2)
                confidence = max(0.5, min(0.99, confidence + 0.5))

                violation_id = Violation.create(
                    violation_type=violation_type,
                    confidence=confidence,
                    severity=severity,
                    screenshot_path=screenshot_path,
                    compliance_score=worker["compliance_score"],
                    worker_bbox=list(worker["box"]),
                    camera_id=self.camera_id,
                    session_id=self.session_id,
                )
                logged.append(Violation.get(violation_id))
        return logged

    def _save_screenshot(self, frame, worker, violation_type):
        filename = timestamped_filename(prefix=violation_type)
        filepath = self.violations_dir / filename
        annotated = frame.copy()
        x1, y1, x2, y2 = worker["box"]
        cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 0, 255), 3)
        cv2.putText(
            annotated, violation_type.upper().replace("_", " "),
            (x1, max(20, y1 - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2,
        )
        cv2.imwrite(str(filepath), annotated)
        return f"violations/{filename}"

    @staticmethod
    def _overlay_compliance(frame, workers):
        y = 24
        for i, worker in enumerate(workers):
            x1, y1, x2, y2 = worker["box"]
            score = worker["compliance_score"]
            color = (0, 200, 0) if score == 100 else (0, 165, 255) if score >= 60 else (0, 0, 255)
            cv2.putText(
                frame, f"Compliance: {score}%",
                (x1, max(15, y1 - 26)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2,
            )
        return frame
