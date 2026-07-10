# Industrial AI Vision

**Developed by:** Prathistha Beniwal

**AI-Powered Industrial Safety Monitoring Platform** — real-time PPE
(helmet / vest / boots) compliance detection with a full software platform
around it: dashboard, evidence gallery, analytics, REST API, and generated
incident reports.

This project began as a small computer-vision prototype (`work.py`, a single
script that ran YOLOv8 over a webcam or video file). It has since been
rebuilt into a layered, production-shaped Flask application — the CLI
prototype still works and now shares its detection code with the web
platform, it hasn't been thrown away.

---

## Features

- **Multi-source detection** — webcam, uploaded video, or CCTV/RTSP stream,
  all through the same pipeline.
- **PPE detection** — person, helmet, vest, boots; automatically flags
  missing helmet / vest / boots per worker.
- **Live dashboard** — live annotated feed, today's violations, workers
  detected, per-item compliance %, recent alerts, active camera count.
- **Violation management** — every violation is saved with a screenshot,
  timestamp, confidence, violation type, and camera, in SQLite.
- **Evidence gallery** — filter saved screenshots by date, violation type,
  and confidence.
- **Analytics** — daily / weekly / monthly violation trends and compliance
  trend charts (Chart.js).
- **REST API** — `GET /api/dashboard`, `GET /api/violations`,
  `GET /api/analytics`, `GET /api/reports`, `POST /api/upload`, plus camera
  and status-management endpoints. See [`docs/API.md`](docs/API.md).
- **Incident reports** — one click generates a professional PDF report
  (incident ID, time, violation, severity, confidence, recommended action);
  CSV export for the full violation log.
- **Compliance score** — per-worker score (e.g. helmet ✓, vest ✓, boots ✗ →
  67%), computed from which PPE items were detected.
- **Authentication** — session-based login/logout; all dashboard and API
  routes require sign-in.
- **SQLite** — auto-initializing schema, no manual migration step needed.

## Tech stack

Python · Flask · YOLOv8 (Ultralytics) · OpenCV · SQLite · HTML · CSS ·
JavaScript · Bootstrap · Chart.js

## Quick start

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python run.py
```

Open `http://localhost:5000`, sign in with `admin` / `admin123` (change
this — see [`docs/INSTALLATION.md`](docs/INSTALLATION.md)), upload a clip or
start a webcam feed, and watch violations populate the dashboard.

Full setup instructions, environment variables, and GPU notes:
[`docs/INSTALLATION.md`](docs/INSTALLATION.md)

## Folder structure

See [`docs/FOLDER_STRUCTURE.md`](docs/FOLDER_STRUCTURE.md) for the full
layout. Summary:

```
app/{routes,services,models,database,utils,templates,static}
violations/   reports/   uploads/   database/
work.py       run.py     requirements.txt
```

## Architecture

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full data-flow
diagram (camera → OpenCV → YOLOv8 → compliance engine → SQLite → REST API →
dashboard) and the reasoning behind the layered design, the process-wide
model singleton, and the cooldown-based deduplication strategy that keeps
one ongoing violation from flooding the database.

## API documentation

See [`docs/API.md`](docs/API.md).

## Notes on the bundled model

The repository ships `yolov8n.pt` (generic COCO weights) so the whole
pipeline is runnable immediately. Because COCO has no helmet/vest/boot
classes, the platform falls back to a proportional body-zone heuristic to
approximate PPE presence when no PPE-trained weights are found — this keeps
every downstream feature (violations, screenshots, compliance scoring,
reports) fully exercisable out of the box. Dropping a fine-tuned
`yolov8n-ppe.pt` / `best.pt` / `ppe.pt` into the project root switches to
real PPE detection automatically, no code changes required.

## Future enhancements

See [`docs/FUTURE_ENHANCEMENTS.md`](docs/FUTURE_ENHANCEMENTS.md).

## Development history (representative commits)

This is the commit history this codebase was built against, for reference
when working in it further:

```
feat: scaffold Flask app factory, config, and blueprint structure
feat: add SQLite schema + auto-init (users, cameras, sessions, violations, reports)
feat: port YOLOv8 detection logic from work.py into DetectionEngine service
feat: add per-worker compliance scoring and severity classification
feat: add ViolationPipeline (frame-skip, duplicate-frame elision, cooldown-based logging)
feat: add MJPEG live-stream route for webcam/upload/CCTV sources
feat: add session-based auth (login/logout, login_required decorator)
feat: build dashboard page + /api/dashboard summary endpoint
feat: build evidence gallery with date/type/confidence filtering
feat: build analytics page + Chart.js daily/weekly/monthly/compliance charts
feat: add incident report generation (PDF via reportlab) + CSV export
feat: build landing page (hero, features, architecture, stack, demo, about)
chore: add requirements.txt, .gitignore, MIT license
docs: add architecture, API, installation, folder structure, future enhancements
refactor: keep work.py CLI tool working, delegate to shared DetectionEngine
```

## License

MIT — see [`LICENSE`](LICENSE).
