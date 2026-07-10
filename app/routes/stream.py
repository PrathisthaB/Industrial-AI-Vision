"""
Live detection feed — streams annotated MJPEG frames to the dashboard for
webcam, uploaded video, and CCTV (RTSP/HTTP) sources alike, running every
frame through the shared ViolationPipeline so violations are logged in
real time regardless of source type.
"""

import cv2
from flask import Blueprint, Response, current_app, jsonify, stream_with_context

from app.utils.decorators import login_required
from app.models import Camera, Session
from app.services.violation_service import ViolationPipeline

bp = Blueprint("stream", __name__)


def _open_capture(camera):
    source_type = camera["source_type"]
    source_path = camera["source_path"]

    if source_type == "webcam":
        try:
            index = int(source_path)
        except (TypeError, ValueError):
            index = 0
        return cv2.VideoCapture(index)

    # "upload" (local file path) and "cctv" (RTSP/HTTP URL) both open the
    # same way via OpenCV's VideoCapture.
    return cv2.VideoCapture(source_path)


def _generate_stream(app, camera_id):
    with app.app_context():
        camera = Camera.get(camera_id)
        if camera is None:
            return

        cap = _open_capture(camera)
        session_id = Session.start(
            source_type=camera["source_type"],
            source_label=camera["name"],
            camera_id=camera["id"],
        )
        pipeline = ViolationPipeline(app, camera_id=camera["id"], session_id=session_id)

        try:
            while True:
                ok, frame = cap.read()
                if not ok:
                    # Loop uploaded/CCTV footage so the demo stream keeps
                    # running; webcams simply end the generator on disconnect.
                    if camera["source_type"] == "webcam":
                        break
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ok, frame = cap.read()
                    if not ok:
                        break

                annotated, _new_violations, _workers = pipeline.process_frame(frame)

                ok, buffer = cv2.imencode(
                    ".jpg", annotated, [int(cv2.IMWRITE_JPEG_QUALITY), 80]
                )
                if not ok:
                    continue

                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"
                )
        finally:
            cap.release()
            Session.finish(session_id)


@bp.route("/stream/<int:camera_id>")
@login_required
def live_feed(camera_id):
    app = current_app._get_current_object()
    camera = Camera.get(camera_id)
    if camera is None:
        return jsonify({"error": "camera not found"}), 404

    return Response(
        _generate_stream(app, camera_id),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )
