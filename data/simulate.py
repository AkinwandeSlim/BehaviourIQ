# data/simulate.py
import os
import random
import pandas as pd
from faker import Faker

fake = Faker()

CATEGORIES = ["tech", "fashion", "food", "fitness", "travel", "finance"]
ACTIONS = ["view", "click", "search", "purchase", "skip", "save"]

def generate_user_session(user_id, n=20):
    events = []
    preferred = random.sample(CATEGORIES, 2)  # each user has 2 affinities
    for _ in range(n):
        cat = random.choices(
            CATEGORIES,
            weights=[5 if c in preferred else 1 for c in CATEGORIES]
        )[0]
        events.append({
            "user_id": user_id,
            "action": random.choice(ACTIONS),
            "category": cat,
            "item": fake.word(),
            "timestamp": fake.date_time_this_month().isoformat(),
            "dwell_seconds": random.randint(2, 120)
        })
    return events

if __name__ == "__main__":
    # Always saves to the data/ folder relative to this file's location
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "user_events.csv")

    all_events = []
    for i in range(1, 11):
        all_events.extend(generate_user_session(f"user_{i:03d}"))

    df = pd.DataFrame(all_events)
    df.to_csv(output_path, index=False)
    print(f"✅ Generated {len(df)} events for {df['user_id'].nunique()} users")
    print(f"📁 Saved to: {output_path}")
    print(df.head())