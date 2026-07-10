# Folder Structure

```
industrial-ai-vision/
├── app/
│   ├── __init__.py            # Application factory (create_app)
│   ├── config.py              # Environment-driven configuration
│   ├── routes/                # Flask Blueprints (HTTP layer only)
│   │   ├── main.py            # Landing page
│   │   ├── auth.py            # Login / logout
│   │   ├── dashboard.py       # Dashboard page
│   │   ├── violations.py      # Evidence gallery page + screenshot serving
│   │   ├── analytics.py       # Analytics page
│   │   ├── reports.py         # Incident report pages + PDF/CSV export
│   │   ├── upload.py          # Video upload form handling
│   │   ├── stream.py          # MJPEG live detection feed
│   │   └── api.py             # REST API (/api/*)
│   ├── services/              # Business logic, no HTTP or SQL specifics
│   │   ├── detection_service.py    # YOLOv8 wrapper, compliance scoring
│   │   ├── violation_service.py    # Frame pipeline → persisted violations
│   │   ├── analytics_service.py    # Trend/aggregate computations
│   │   └── report_service.py       # Incident report + PDF/CSV generation
│   ├── models/                 # Data-access objects over SQLite
│   │   ├── user.py
│   │   ├── camera.py
│   │   ├── violation.py
│   │   └── session.py          # Session, IncidentReport, DailyStats
│   ├── database/
│   │   ├── schema.sql          # Full DDL, applied automatically at startup
│   │   └── db.py                # Connection management + seeding
│   ├── utils/
│   │   ├── decorators.py       # login_required, roles_required
│   │   └── helpers.py
│   ├── templates/               # Jinja2 templates
│   │   ├── base.html            # Authenticated app shell (sidebar)
│   │   ├── landing.html         # Public marketing page
│   │   ├── login.html
│   │   ├── dashboard.html
│   │   ├── violations.html
│   │   ├── analytics.html
│   │   └── reports.html
│   └── static/
│       ├── css/style.css
│       └── js/app.js
├── violations/                 # Auto-created: saved evidence screenshots
├── reports/                    # Auto-created: generated PDF incident reports
├── uploads/                    # Auto-created: uploaded video files
├── database/                   # Auto-created: safety_platform.db (SQLite)
├── docs/                       # This documentation set
├── work.py                     # Standalone CLI PPE-detection tool (kept from original prototype)
├── run.py                      # Application entry point
├── requirements.txt
├── .gitignore
├── LICENSE                     # MIT
└── README.md
```
