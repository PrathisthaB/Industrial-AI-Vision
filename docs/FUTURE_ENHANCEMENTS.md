# Future Enhancements

Ideas for extending the platform beyond its current scope, roughly ordered
by expected impact:

## Detection quality
- Fine-tune a dedicated PPE-detection YOLOv8 model (helmet/vest/boots as
  first-class classes) on a labeled industrial dataset, instead of relying
  on the COCO-fallback proportional-zone heuristic.
- Add tracking (e.g. ByteTrack/DeepSORT) so a single worker is followed
  across frames instead of being re-identified every inference pass —
  enables per-worker violation history and reduces double-counting further.
- Multi-camera calibration for accurate zone boundaries per site.

## Platform / scale
- Move from SQLite to PostgreSQL for multi-instance deployments.
- Move violation screenshots and generated reports to object storage (S3 /
  GCS) instead of local disk.
- Background job queue (Celery/RQ) for video-upload processing instead of
  processing inline during the MJPEG stream.
- WebSocket-based push updates for the dashboard instead of 15s polling.

## Product
- Role-based dashboards (EHS manager vs. floor supervisor vs. auditor view).
- Slack/Teams/SMS alerting on critical violations.
- Shift-based compliance reporting and per-worker compliance history (with
  appropriate privacy/consent handling).
- Configurable violation severity rules and cooldown windows per site.
- Multi-tenant support for monitoring multiple facilities from one instance.

## Security / compliance
- Two-factor authentication and audit logging of who reviewed/resolved each
  violation.
- Configurable data-retention policy for evidence screenshots.
- Formal privacy review if deploying anywhere workers can be personally
  identified (face blurring option for stored evidence).
