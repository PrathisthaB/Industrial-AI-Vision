#!/usr/bin/env python3
"""
work.py — standalone CLI PPE detection tool.

This is the original command-line prototype this platform grew out of,
kept and cleaned up (no functionality removed) for quick, dependency-light
testing of the detection pipeline without running the full Flask app:

    python work.py path/to/video.mp4
    python work.py --webcam 0

It now delegates the actual inference/compliance logic to
`app.services.detection_service` so both the CLI tool and the web platform
share exactly one detection implementation instead of drifting apart.
"""

import sys
import argparse
import glob
from pathlib import Path

import cv2

# Allow running this script directly from the project root.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.services.detection_service import (
    DetectionEngine,
    draw_detections,
    compute_worker_compliance,
)

OUTPUT_VIDEO = "output_detected.mp4"
INFER_SIZE = 640
CONF_THRESHOLD = 0.35
IOU_THRESHOLD = 0.45
COCO_MODEL = "yolov8n.pt"
PPE_MODEL_CANDIDATES = ["yolov8n-ppe.pt", "best.pt", "ppe.pt"]


def find_input_video(user_path=None):
    if user_path:
        return user_path
    for ext in ["*.mp4", "*.avi", "*.mov", "*.mkv"]:
        matches = glob.glob(ext)
        if matches:
            return matches[0]
    print("No video file found. Pass a path or use --webcam.")
    sys.exit(1)


def annotate_frame(engine, frame):
    detections = engine.infer(frame)
    workers = compute_worker_compliance(detections)
    frame = draw_detections(frame, detections)
    for w in workers:
        x1, y1, _, _ = w["box"]
        color = (0, 200, 0) if w["compliance_score"] == 100 else (0, 0, 255)
        cv2.putText(frame, f"Compliance: {w['compliance_score']}%",
                    (x1, max(15, y1 - 24)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    return frame, workers


def process_video(path, engine):
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        print(f"Could not open video: {path}")
        sys.exit(1)

    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0

    writer = cv2.VideoWriter(OUTPUT_VIDEO, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))

    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame, _workers = annotate_frame(engine, frame)
        writer.write(frame)
        cv2.imshow("PPE Detection", frame)
        frame_count += 1

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    print(f"Processed {frame_count} frames. Output saved to {OUTPUT_VIDEO}")
    cap.release()
    writer.release()
    cv2.destroyAllWindows()


def process_webcam(index, engine):
    cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        print(f"Could not open webcam index {index}")
        sys.exit(1)

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame, _workers = annotate_frame(engine, frame)
        cv2.imshow("PPE Detection", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


def main():
    parser = argparse.ArgumentParser(description="Standalone PPE detection CLI tool.")
    parser.add_argument("video", nargs="?", default=None, help="Path to a video file.")
    parser.add_argument("--webcam", nargs="?", const=0, type=int, help="Webcam device index.")
    args = parser.parse_args()

    engine = DetectionEngine(
        model_path=COCO_MODEL,
        ppe_candidates=PPE_MODEL_CANDIDATES,
        infer_size=INFER_SIZE,
        conf=CONF_THRESHOLD,
        iou=IOU_THRESHOLD,
    )
    print(f"Loaded {'PPE-trained' if engine.is_ppe_model else 'COCO fallback'} model "
          f"on device={engine.device}")

    if args.webcam is not None:
        process_webcam(args.webcam, engine)
    else:
        video_path = find_input_video(args.video)
        process_video(video_path, engine)


if __name__ == "__main__":
    main()
