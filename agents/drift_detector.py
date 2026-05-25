"""
agents/drift_detector.py — Lightweight concept drift detection for BehaviorIQ.

Tracks buying_stage transitions per user across agent runs and flags
meaningful shifts (e.g. awareness → ready_to_buy) in real time.

In-memory store per session. Replace _drift_log with Redis for
cross-session persistence in production.
"""

from datetime import datetime

# In-memory snapshot store  {user_id: [snapshot, ...]}
_drift_log: dict[str, list] = {}

# Funnel order — higher index = closer to purchase
STAGE_ORDER: dict[str, int] = {
    "awareness":     0,
    "consideration": 1,
    "ready_to_buy":  2,
    "repeat_buyer":  3,
}


def record_prediction(user_id: str, prediction: dict) -> dict | None:
    """
    Store the latest prediction snapshot for *user_id*.

    Returns a drift event dict if the buying_stage has changed since the
    last snapshot, or None if this is the first run / no change detected.

    Drift event schema:
        user_id     str   — user that drifted
        from_stage  str   — previous buying_stage
        to_stage    str   — new buying_stage
        direction   str   — "⬆️ progressed" | "⬇️ regressed"
        delta       int   — signed stage index change
        confidence  float — confidence of new prediction
        detected_at str   — ISO-8601 UTC timestamp
        message     str   — human-readable markdown summary
    """
    stage      = prediction.get("buying_stage", "awareness")
    confidence = prediction.get("confidence", 0.0)
    now        = datetime.utcnow().isoformat()

    history    = _drift_log.setdefault(user_id, [])
    drift_event: dict | None = None

    if history:
        prev       = history[-1]
        prev_stage = prev["buying_stage"]
        prev_idx   = STAGE_ORDER.get(prev_stage, 0)
        curr_idx   = STAGE_ORDER.get(stage, 0)
        delta      = curr_idx - prev_idx

        if delta != 0:
            direction   = "⬆️ progressed" if delta > 0 else "⬇️ regressed"
            from_label  = prev_stage.replace("_", " ").title()
            to_label    = stage.replace("_", " ").title()
            drift_event = {
                "user_id":     user_id,
                "from_stage":  prev_stage,
                "to_stage":    stage,
                "direction":   direction,
                "delta":       delta,
                "confidence":  confidence,
                "detected_at": now,
                "message": (
                    f"`{user_id}` {direction} from "
                    f"**{from_label}** → **{to_label}** "
                    f"({confidence:.0%} confidence)"
                ),
            }

    history.append({
        "buying_stage": stage,
        "confidence":   confidence,
        "recorded_at":  now,
    })

    # Keep only the last 10 snapshots per user to cap memory
    _drift_log[user_id] = history[-10:]

    return drift_event


def get_drift_history(user_id: str) -> list[dict]:
    """Return the full snapshot history for *user_id* (oldest first)."""
    return _drift_log.get(user_id, [])


def get_all_drift_events() -> dict[str, list]:
    """Return the raw log for all users (useful for a global drift dashboard)."""
    return dict(_drift_log)


def clear_history(user_id: str | None = None) -> None:
    """Clear history for one user or all users if user_id is None."""
    if user_id is None:
        _drift_log.clear()
    else:
        _drift_log.pop(user_id, None)