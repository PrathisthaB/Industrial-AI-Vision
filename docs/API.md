# API Documentation

All endpoints below (except `/health` and the auth pages) require an active
session — sign in via `POST /login` first (the browser session cookie is
sent automatically on subsequent requests; for programmatic use, keep the
`session` cookie between requests).

Base URL (local dev): `http://localhost:5000`

## Auth

| Method | Path       | Description                              |
|--------|------------|-------------------------------------------|
| GET    | `/login`   | Login form                                 |
| POST   | `/login`   | Authenticate (`username`, `password`)      |
| GET    | `/logout`  | Clear the session                          |

## Dashboard

### `GET /api/dashboard`
Returns summary cards for the dashboard.

```json
{
  "violations_today": 4,
  "workers_detected": 12,
  "helmet_compliance": 91.7,
  "vest_compliance": 96.0,
  "boot_compliance": 100.0,
  "active_cameras": 2,
  "recent_alerts": [ { "id": 41, "violation_type": "missing_helmet", "...": "..." } ]
}
```

## Violations

### `GET /violations` (`?date_from&date_to&type&min_confidence`) — HTML gallery, evidence page.

### `GET /api/violations`
Query params: `date_from`, `date_to`, `type`, `min_confidence`, `camera_id`,
`limit` (default 50, max 200), `offset`.

```json
{ "count": 2, "results": [ { "id": 12, "violation_type": "missing_vest", "confidence": 0.83, "severity": "medium", "screenshot_path": "violations/missing_vest_20260710_101500_123456.jpg", "timestamp": "2026-07-10 10:15:00" } ] }
```

### `GET /api/violations/<id>`
Single violation record.

### `POST /api/violations/<id>/status`
Body: `{ "status": "open" | "reviewed" | "resolved" }`

## Analytics

### `GET /api/analytics` (`?days=30`)
```json
{
  "daily": [ { "date": "2026-07-01", "count": 3 } ],
  "weekly": [ { "week": "2026-W27", "count": 14 } ],
  "monthly": [ { "month": "2026-07", "count": 39 } ],
  "compliance_trend": [ { "date": "2026-07-01", "helmet": 92.0, "vest": 97.0, "boots": 100.0 } ],
  "breakdown": { "missing_helmet": 20, "missing_vest": 9, "missing_boots": 3 }
}
```

## Reports

### `GET /api/reports`
Lists all generated incident reports.

### `POST /api/reports/<violation_id>/generate`
Generates a PDF incident report for a violation and returns the report
record (id, incident_code, severity, recommended_action, file_path).

### `GET /reports/<id>/download`
Downloads the generated PDF.

### `GET /reports/export.csv`
Exports up to 1000 violation rows as CSV.

## Upload

### `POST /api/upload`
`multipart/form-data` with fields:
- `video` (required) — mp4/avi/mov/mkv file
- `camera_name` (optional)
- `location` (optional)

```json
{ "ok": true, "camera_id": 3, "stream_url": "/stream/3" }
```

## Cameras

### `GET /api/cameras`
Lists all configured camera sources (webcam / upload / cctv).

### `POST /api/cameras`
Register a CCTV/RTSP stream or another logical camera.
```json
{ "name": "Loading Dock", "source_type": "cctv", "source_path": "rtsp://192.168.1.50/stream1", "location": "Dock 3" }
```

## Live stream

### `GET /stream/<camera_id>`
MJPEG stream (`multipart/x-mixed-replace`) of the annotated live feed for a
camera. Embed directly in an `<img>` tag. Violations are logged to the
database in real time as frames are processed.

## Health

### `GET /health`
Unauthenticated liveness check: `{ "status": "ok", "service": "industrial-ai-vision" }`
