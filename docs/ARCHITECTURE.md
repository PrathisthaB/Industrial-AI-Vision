# Architecture

## Overview

Industrial AI Vision is a layered Flask application. Each layer has one job,
which keeps the computer-vision code, the persistence code, and the HTTP
routes independently testable.

```
                        ┌─────────────────────────────┐
                        │        Presentation          │
                        │  templates/ + static/ (JS)    │
                        └───────────────┬───────────────┘
                                        │
                        ┌───────────────▼───────────────┐
                        │            Routes             │
                        │  app/routes/*.py (Blueprints)  │
                        │  auth · dashboard · api · ...  │
                        └───────────────┬───────────────┘
                                        │
                        ┌───────────────▼───────────────┐
                        │            Services            │
                        │  app/services/*.py              │
                        │  detection · violation ·         │
                        │  analytics · report              │
                        └───────────────┬───────────────┘
                                        │
                        ┌───────────────▼───────────────┐
                        │             Models              │
                        │  app/models/*.py (data access)   │
                        └───────────────┬───────────────┘
                                        │
                        ┌───────────────▼───────────────┐
                        │            Database              │
                        │  SQLite — app/database/schema.sql │
                        └─────────────────────────────────┘
```

## Detection pipeline

```
Camera / Upload / CCTV
        │  cv2.VideoCapture
        ▼
Frame read ── duplicate/skip check (FRAME_SKIP, DUPLICATE_FRAME_THRESHOLD)
        │
        ▼
YOLOv8 inference (DetectionEngine.infer)
        │  falls back to COCO person detection + proportional PPE zones
        │  when no PPE-trained weights are present (see README)
        ▼
Per-worker compliance scoring (compute_worker_compliance)
        │  groups helmet/vest/boots detections under each person box
        ▼
Cooldown check (CooldownTracker) ── suppress duplicate logging of an
        │                            ongoing violation
        ▼
Violation persisted + evidence screenshot saved (ViolationPipeline)
        │
        ▼
Annotated frame streamed back to the browser as MJPEG (/stream/<camera_id>)
```

## Key design decisions

- **Single detection implementation.** Both the Flask app
  (`app/services/detection_service.py`) and the standalone `work.py` CLI tool
  share the same `DetectionEngine` class, so there is exactly one place that
  understands YOLO output.
- **Process-wide model singleton.** `DetectionEngine.get_instance()` loads the
  (large) YOLO weights once per process rather than once per request/session.
- **No ORM.** A thin data-access layer (`app/models/`) wraps raw `sqlite3`
  calls. This keeps the dependency footprint small and the SQL visible and
  auditable — appropriate for a project of this size.
- **Cooldown-based deduplication.** A worker standing without a helmet for 30
  seconds should produce one incident, not one row per frame. Each
  `(camera_id, violation_type)` pair has its own cooldown window
  (`VIOLATION_COOLDOWN_SECONDS`, default 8s).
- **Session-based auth**, not JWT — this is a server-rendered dashboard, not a
  distributed API-first product, so cookie sessions are the simpler correct
  choice.

## Request flow example: viewing the dashboard

1. Browser requests `GET /dashboard`.
2. `login_required` decorator checks `session["user_id"]`; redirects to
   `/login` if absent.
3. `dashboard.index` route calls `analytics_service.dashboard_summary()`.
4. That service queries `Violation`, `Session`, and `Camera` models.
5. The route renders `dashboard.html`, which also opens an MJPEG stream via
   `<img src="/stream/<camera_id>">` for the live feed panel.
6. The browser polls `GET /api/dashboard` every 15s to refresh summary data
   without a full page reload.
