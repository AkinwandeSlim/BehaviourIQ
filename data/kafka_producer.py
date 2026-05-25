# data/kafka_producer.py
"""
REAL Kafka producer — run this in a second terminal during the demo.

Usage:
    cd C:\MyFiles\DOCUMENT-2026\2026\May2026\behavioriq
    venv\Scripts\activate
    python data/kafka_producer.py

Requirements:
    pip install kafka-python
    Kafka must be running locally on localhost:9092

Quick Kafka setup (Windows — if not already installed):
    Download kafka_2.13-3.7.0 from kafka.apache.org
    In terminal 1: .\bin\windows\zookeeper-server-start.bat .\config\zookeeper.properties
    In terminal 2: .\bin\windows\kafka-server-start.bat .\config\server.properties
    In terminal 3: python data/kafka_producer.py
    In terminal 4: streamlit run app.py
"""

import os
import sys
import json
import time
import pandas as pd

TOPIC      = os.getenv("KAFKA_TOPIC",     "behavioriq-events")
BOOTSTRAP  = os.getenv("KAFKA_BOOTSTRAP", "localhost:9094")   # localhost:9094 when running on host
DELAY      = float(os.getenv("PRODUCER_DELAY", "0.5"))
LOOP       = os.getenv("PRODUCER_LOOP", "true").lower() == "true"

# ── Paths ──────────────────────────────────────────────────────────────────────
_BASE     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CSV_PATH = os.path.join(_BASE, "data", "user_events.csv")
sys.path.insert(0, _BASE)


def main():
    try:
        from kafka import KafkaProducer
    except ImportError:
        print("❌ kafka-python not installed. Run: pip install kafka-python")
        sys.exit(1)

    try:
        producer = KafkaProducer(
            bootstrap_servers=BOOTSTRAP,
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
        )
        print(f"✅ Connected to Kafka at {BOOTSTRAP}")
    except Exception as e:
        print(f"❌ Could not connect to Kafka: {e}")
        print("   Make sure Kafka is running on localhost:9092")
        sys.exit(1)

    # Load and enrich dataset
    df = pd.read_csv(_CSV_PATH, parse_dates=["timestamp"])
    df["categoryid"] = df["categoryid"].astype(str)
    df["itemid"]     = df["itemid"].astype(str)

    try:
        from data.category_map import enrich_dataframe
        df = enrich_dataframe(df)
    except Exception:
        df["category_name"] = "Category " + df["categoryid"]

    df = df.sort_values("timestamp").reset_index(drop=True)
    print(f"▶ Replaying {len(df):,} events → topic '{TOPIC}' (delay={DELAY}s)")
    print("  Press Ctrl+C to stop\n")

    sent = 0
    while True:
        for _, row in df.iterrows():
            event = {
                "user_id":      row["user_id"],
                "action":       row["action"],
                "category":     row.get("category_name", row["categoryid"]),
                "item_id":      row["itemid"],
                "hour":         int(row["hour_of_day"]),
                "is_weekend":   int(row["is_weekend"]),
                "available":    int(row["item_available"]),
                "has_purchase": bool(pd.notna(row.get("transactionid"))),
                "timestamp":    str(row["timestamp"]),
            }
            producer.send(TOPIC, event)
            sent += 1

            action_icon = {"view": "👁", "addtocart": "🛒", "transaction": "💳"}.get(
                row["action"], "·"
            )
            print(
                f"  {action_icon} [{sent:>5}] {row['user_id']} | "
                f"{row['action']:<12} | {event['category']}"
            )
            time.sleep(DELAY)

        if not LOOP:
            break
        print("\n↩ Dataset complete — looping from start...\n")

    producer.flush()
    print(f"\n✅ Done — {sent:,} events sent.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n■ Producer stopped by user.")