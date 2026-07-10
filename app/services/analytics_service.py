"""
Analytics service — aggregates violation/session data into the shapes the
dashboard, analytics page, and REST API need (daily/weekly/monthly trends,
compliance percentages, recent alerts).
"""

from datetime import datetime, timedelta

from app.models import Violation, Session, Camera, DailyStats


PPE_ITEMS = ["helmet", "vest", "boots"]


def _compliance_pct(total_workers, violation_count):
    if total_workers <= 0:
        return 100.0
    pct = 100.0 - (violation_count / max(1, total_workers)) * 100.0
    return round(max(0.0, min(100.0, pct)), 1)


def dashboard_summary():
    """Everything the main dashboard cards need in one call."""
    violations_today = Violation.count_today()
    workers_today = Session.total_workers_today()
    counts_by_type = Violation.counts_by_type(date_from=_today())

    helmet_violations = counts_by_type.get("missing_helmet", 0)
    vest_violations = counts_by_type.get("missing_vest", 0)
    boot_violations = counts_by_type.get("missing_boots", 0)

    return {
        "violations_today": violations_today,
        "workers_detected": workers_today,
        "helmet_compliance": _compliance_pct(workers_today, helmet_violations),
        "vest_compliance": _compliance_pct(workers_today, vest_violations),
        "boot_compliance": _compliance_pct(workers_today, boot_violations),
        "active_cameras": Camera.count_active(),
        "recent_alerts": Violation.recent(limit=8),
    }


def _today():
    return datetime.now().strftime("%Y-%m-%d")


def trend_series(days=30):
    """Daily violation counts for the last N days, zero-filled for gaps."""
    raw = {r["day"]: r["count"] for r in Violation.counts_by_day(days=days)}
    series = []
    for i in range(days - 1, -1, -1):
        day = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        series.append({"date": day, "count": raw.get(day, 0)})
    return series


def weekly_series(weeks=12):
    """Aggregate the daily trend into ISO week buckets."""
    daily = trend_series(days=weeks * 7)
    buckets = {}
    for point in daily:
        dt = datetime.strptime(point["date"], "%Y-%m-%d")
        year, week, _ = dt.isocalendar()
        key = f"{year}-W{week:02d}"
        buckets.setdefault(key, 0)
        buckets[key] += point["count"]
    return [{"week": k, "count": v} for k, v in sorted(buckets.items())]


def monthly_series(months=12):
    daily = trend_series(days=months * 31)
    buckets = {}
    for point in daily:
        key = point["date"][:7]  # YYYY-MM
        buckets.setdefault(key, 0)
        buckets[key] += point["count"]
    sorted_items = sorted(buckets.items())[-months:]
    return [{"month": k, "count": v} for k, v in sorted_items]


def compliance_trend(days=14):
    """Per-day compliance percentage for helmet/vest/boots for charting."""
    daily = DailyStats.range(days=days)
    if daily:
        return [
            {
                "date": row["date"],
                "helmet": row["helmet_compliance"],
                "vest": row["vest_compliance"],
                "boots": row["boot_compliance"],
            }
            for row in daily
        ]

    # Fall back to computing on the fly from raw violation counts if the
    # daily_stats rollup table hasn't been populated yet.
    results = []
    for i in range(days - 1, -1, -1):
        day = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        counts = Violation.counts_by_type(date_from=day, date_to=day)
        workers = Session.total_workers_today() if i == 0 else 0
        results.append({
            "date": day,
            "helmet": _compliance_pct(max(workers, 1), counts.get("missing_helmet", 0)),
            "vest": _compliance_pct(max(workers, 1), counts.get("missing_vest", 0)),
            "boots": _compliance_pct(max(workers, 1), counts.get("missing_boots", 0)),
        })
    return results


def violation_type_breakdown():
    return Violation.counts_by_type()


def overall_compliance_score(violation_row):
    """
    Compute the example-style compliance score for a single violation record,
    e.g. Helmet OK, Vest OK, Boots missing -> 67%.
    """
    if violation_row.get("compliance_score") is not None:
        return violation_row["compliance_score"]
    return 100


def refresh_daily_stats():
    """Recompute today's rollup row in daily_stats (call periodically / on demand)."""
    today = _today()
    counts = Violation.counts_by_type(date_from=today, date_to=today)
    workers = Session.total_workers_today()
    helmet_v = counts.get("missing_helmet", 0)
    vest_v = counts.get("missing_vest", 0)
    boots_v = counts.get("missing_boots", 0)

    DailyStats.upsert(
        today,
        total_workers=workers,
        total_violations=sum(counts.values()),
        missing_helmet=helmet_v,
        missing_vest=vest_v,
        missing_boots=boots_v,
        helmet_compliance=_compliance_pct(workers, helmet_v),
        vest_compliance=_compliance_pct(workers, vest_v),
        boot_compliance=_compliance_pct(workers, boots_v),
    )
