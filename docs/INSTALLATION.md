# Installation Guide

## Prerequisites

- Python 3.10+
- pip
- (Optional) A CUDA-capable GPU for faster inference — the app auto-detects
  and falls back to CPU otherwise.
- (Optional) A webcam for live testing.

## 1. Clone and enter the project

```bash
git clone https://github.com/<your-org>/industrial-ai-vision.git
cd industrial-ai-vision
```

## 2. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

> **Note on PyTorch:** the pinned `torch`/`torchvision` versions target CPU
> and generic CUDA wheels. If you have a specific CUDA version, follow the
> official selector at https://pytorch.org/get-started/locally/ and install
> the matching wheel before running `pip install -r requirements.txt`.

## 4. (Optional) Add a PPE-trained model

By default the platform runs on the bundled `yolov8n.pt` (generic COCO
weights) and approximates PPE presence using proportional body zones so the
whole pipeline is demoable out of the box. For real accuracy, drop a
fine-tuned PPE detector weights file into the project root named one of:

```
yolov8n-ppe.pt
best.pt
ppe.pt
```

The app automatically prefers whichever of these is present.

## 5. Run the app

```bash
python run.py
```

Visit `http://localhost:5000`. The SQLite database and folder structure
(`database/`, `violations/`, `reports/`, `uploads/`) are created
automatically on first run, along with a default admin account:

```
username: admin
password: admin123
```

**Change this password (or set `ADMIN_USERNAME` / `ADMIN_PASSWORD` env vars
before first run) before deploying anywhere reachable by others.**

## 6. Environment variables (optional)

| Variable         | Default                              | Purpose                          |
|------------------|----------------------------------------|-----------------------------------|
| `SECRET_KEY`     | dev key                                | Flask session signing key          |
| `FLASK_ENV`      | `development`                          | `development` / `production`       |
| `PORT`           | `5000`                                 | HTTP port                          |
| `DATABASE_PATH`  | `database/safety_platform.db`          | SQLite file location                |
| `ADMIN_USERNAME` | `admin`                                | Seeded admin username               |
| `ADMIN_PASSWORD` | `admin123`                             | Seeded admin password               |

## 7. Running the standalone CLI tool

For quick testing without the web UI:

```bash
python work.py path/to/video.mp4
python work.py --webcam 0
```

## 8. Production deployment

```bash
FLASK_ENV=production SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))") \
  gunicorn -w 2 -b 0.0.0.0:8000 'run:app'
```

Put a reverse proxy (nginx) in front for TLS termination and static file
caching in real deployments.
