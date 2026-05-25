# data/live_stream.py
"""
Simulated real-time event stream for BehaviorIQ.

Architecture:
  - A single background thread replays user_events.csv row by row
  - Events go into a module-level per-user buffer (survives Streamlit rerenders)
  - The Live Feed tab reads from this buffer via get_live_events()

No Kafka server needed — same behaviour, works out of the box.
For real Kafka, swap the producer for kafka_producer.py (separate terminal).
"""

import os
import threading
import time
import pandas as pd
from collections import defaultdict, deque
from datetime import datetime

# ── Shared state (module-level — persists across Streamlit rerenders) ─────────
_lock          = threading.Lock()
_user_buffers  = defaultdict(lambda: deque(maxlen=50))  # last 50 events per user
_global_feed   = deque(maxlen=200)                       # last 200 events across all users
_stats         = {
    "running":    False,
    "total_sent": 0,
    "started_at": None,
    "thread":     None,
}

# ── Paths ─────────────────────────────────────────────────────────────────────
_BASE       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CSV_PATH   = os.path.join(_BASE, "data", "user_events.csv")

# ── Kafka config (read from environment — set by docker-compose) ──────────────
STREAM_MODE      = os.getenv("STREAM_MODE", "simulated")   # "simulated" | "kafka"
KAFKA_BOOTSTRAP  = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
KAFKA_TOPIC      = os.getenv("KAFKA_TOPIC", "behavioriq-events")


# ═══════════════════════════════════════════════════════════════════════════════
# PRODUCER THREAD
# ═══════════════════════════════════════════════════════════════════════════════

def _producer_thread(delay: float, loop: bool):
    """Background thread: replays CSV events into shared buffers."""
    global _stats

    try:
        df = pd.read_csv(_CSV_PATH, parse_dates=["timestamp"])
        df["categoryid"] = df["categoryid"].astype(str)
        df["itemid"]     = df["itemid"].astype(str)

        # Try to import category enrichment — graceful fallback if not available
        try:
            from data.category_map import enrich_dataframe
            df = enrich_dataframe(df)
            has_names = True
        except Exception:
            df["category_name"] = "Category " + df["categoryid"]
            has_names = False

        # Sort by timestamp for realistic replay
        df = df.sort_values("timestamp").reset_index(drop=True)

    except Exception as e:
        print(f"[LiveStream] ERROR loading CSV: {e}")
        with _lock:
            _stats["running"] = False
        return

    print(f"[LiveStream] ▶ Producer started — {len(df):,} events to replay "
          f"(delay={delay}s, loop={loop})")

    while True:
        for _, row in df.iterrows():
            with _lock:
                if not _stats["running"]:
                    print("[LiveStream] ■ Producer stopped.")
                    return

            event = {
                "user_id":       row["user_id"],
                "action":        row["action"],
                "category":      row.get("category_name", row["categoryid"]),
                "item_id":       row["itemid"],
                "hour":          int(row["hour_of_day"]),
                "is_weekend":    int(row["is_weekend"]),
                "available":     int(row["item_available"]),
                "has_purchase":  pd.notna(row.get("transactionid")),
                "stream_ts":     datetime.now().strftime("%H:%M:%S"),
            }

            with _lock:
                _user_buffers[row["user_id"]].append(event)
                _global_feed.append(event)
                _stats["total_sent"] += 1

            time.sleep(delay)

        if not loop:
            break

    with _lock:
        _stats["running"] = False
    print("[LiveStream] ■ Producer finished (end of dataset).")


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════════

def start_stream(delay: float = 0.4, loop: bool = True) -> bool:
    """
    Start the background producer/consumer thread.
    Mode is controlled by the STREAM_MODE env variable:
      'simulated' (default) — replays CSV in-process, no Kafka needed
      'kafka'               — consumes from real Kafka topic (set KAFKA_BOOTSTRAP)
    Returns True if started, False if already running.
    """
    global _stats
    with _lock:
        if _stats["running"]:
            return False
        _stats["running"]    = True
        _stats["total_sent"] = 0
        _stats["started_at"] = datetime.now()

    if STREAM_MODE == "kafka":
        target = _kafka_consumer_thread
        args   = ()
        name   = "KafkaConsumer"
    else:
        target = _producer_thread
        args   = (delay, loop)
        name   = "LiveStreamProducer"

    t = threading.Thread(target=target, args=args, daemon=True, name=name)
    with _lock:
        _stats["thread"] = t
    t.start()
    print(f"[LiveStream] Mode={STREAM_MODE} — thread '{name}' started")
    return True


def _kafka_consumer_thread():
    """Consume real events from Kafka topic — used when STREAM_MODE=kafka."""
    try:
        from kafka import KafkaConsumer
        import json as _json
    except ImportError:
        print("[LiveStream] ❌ kafka-python not installed. Falling back to simulated mode.")
        _producer_thread(0.4, True)
        return

    print(f"[LiveStream] Connecting to Kafka at {KAFKA_BOOTSTRAP}, topic={KAFKA_TOPIC}")
    try:
        consumer = KafkaConsumer(
            KAFKA_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP,
            value_deserializer=lambda m: _json.loads(m.decode("utf-8")),
            auto_offset_reset="earliest",
            group_id="behavioriq-live",
            consumer_timeout_ms=1000,   # allow checking _stats["running"] regularly
        )
    except Exception as e:
        print(f"[LiveStream] ❌ Kafka connection failed: {e} — falling back to simulated mode")
        _producer_thread(0.4, True)
        return

    print(f"[LiveStream] ✅ Kafka consumer connected — listening on '{KAFKA_TOPIC}'")
    while True:
        with _lock:
            if not _stats["running"]:
                break
        try:
            for message in consumer:
                event = message.value
                event["stream_ts"] = datetime.now().strftime("%H:%M:%S")
                uid = event.get("user_id", "unknown")
                with _lock:
                    _user_buffers[uid].append(event)
                    _global_feed.append(event)
                    _stats["total_sent"] += 1
                    if not _stats["running"]:
                        break
        except Exception:
            pass   # consumer_timeout_ms hit — loop and check running flag

    consumer.close()
    print("[LiveStream] ■ Kafka consumer stopped.")


def stop_stream() -> None:
    """Signal the producer thread to stop."""
    with _lock:
        _stats["running"] = False


def is_running() -> bool:
    with _lock:
        return _stats["running"]


def get_stats() -> dict:
    with _lock:
        return {
            "running":    _stats["running"],
            "total_sent": _stats["total_sent"],
            "started_at": _stats["started_at"],
        }


def get_live_events(user_id: str | None = None, n: int = 20) -> list:
    """
    Return the most recent n events.
    If user_id given → events for that user only.
    If user_id is None → global feed across all users.
    """
    with _lock:
        if user_id:
            events = list(_user_buffers.get(user_id, []))
        else:
            events = list(_global_feed)
    return events[-n:]


def get_live_events_df(user_id: str) -> pd.DataFrame:
    """Return live events for a user as a DataFrame (for observe_from_events)."""
    events = get_live_events(user_id, n=50)
    if not events:
        return pd.DataFrame()
    return pd.DataFrame(events)


def get_active_users(top_n: int = 10) -> list[str]:
    """Return users with the most live events so far."""
    with _lock:
        counts = {uid: len(buf) for uid, buf in _user_buffers.items() if buf}
    return sorted(counts, key=counts.get, reverse=True)[:top_n]


def clear_buffers() -> None:
    """Reset all buffers — useful when switching datasets."""
    with _lock:
        _user_buffers.clear()
        _global_feed.clear()
        _stats["total_sent"] = 0