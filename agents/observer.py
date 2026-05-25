# agents/observer.py
# BehaviorIQ ObserverAgent v2
# ─────────────────────────────────────────────────────────────────────────────
# Changes from v1:
#   FIX 1  — zip() replaced with a single aligned groupby (top_product_categories)
#   FIX 2  — live events now resolve category name → ID via reverse lookup before
#             enrich_dataframe() runs, so they get identical enrichment to CSV rows
#   FIX 3  — day_of_week/week_of_month fill uses mode or real current time,
#             not iloc[0] from an unrelated CSV row
#   FIX 4  — build_user_profile_v2 now stores top_department + views + purchases
#   FIX 5  — "Miscellaneous" filtered from top-category and intent signals
#   NEW    — department-level signals, richer recent_summary, _normalize_live_df()

import os
import pandas as pd
from typing import Dict, List, Optional

from memory.vector_store import build_user_profile_v2
from data.category_map import (
    CATEGORY_NAMES,
    get_category_name,
    get_category_names_list,
    to_product_category,
    enrich_dataframe,
    print_mapping_coverage,
    get_department,          # new in v2
    get_breadcrumb,          # new in v2
)

# ── Module-level reverse lookup: display_name → category_id ──────────────────
# Used by _normalize_live_df() to resolve a live event's category string
# ("Electronics & Gadgets") back to a real ID so enrich_dataframe() enriches
# it exactly like a CSV row — avoiding the "Miscellaneous" overwrite bug.
_CATEGORY_NAME_TO_ID: Dict[str, int] = {v: k for k, v in CATEGORY_NAMES.items()}

# Label produced by get_category_name() for any unmapped category ID.
# Filtered out of top-category / intent signals so it doesn't pollute
# recommendations or the ChromaDB profile.
_MISC_LABEL = "Miscellaneous"


class ObserverAgent:
    def __init__(self, events_path: Optional[str] = None):
        if events_path is None:
            base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            events_path = os.path.join(base, "data", "user_events.csv")

        self.df = pd.read_csv(events_path, parse_dates=["timestamp"])
        self.df["categoryid"] = self.df["categoryid"].astype(str)
        self.df["itemid"]     = self.df["itemid"].astype(str)

    # ──────────────────────────────────────────────────────────────────────────
    # PRIVATE — live event normaliser
    # ──────────────────────────────────────────────────────────────────────────
    def _normalize_live_df(
        self, live_events: list, csv_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Convert a list of live event dicts into a DataFrame that matches the
        CSV schema so _build_profile() and enrich_dataframe() work identically
        on live and historical data.

        Key behaviours
        ──────────────
        • Renames live-specific field names to CSV column names.
        • Resolves 'category' string → categoryid via reverse lookup so
          enrich_dataframe() produces the right category_name (FIX 2).
        • Falls back to the raw string as a pre-written category_name only when
          the name is genuinely unknown — rather than overwriting with "Miscellaneous".
        • Fills required columns with real-time values or CSV mode,
          NOT iloc[0] from an arbitrary CSV row (FIX 3).
        """
        live_df = pd.DataFrame(live_events).copy()

        # ── Step 1: rename live-specific fields → CSV schema ─────────────────
        rename_map = {
            "item_id":   "itemid",
            "hour":      "hour_of_day",
            "available": "item_available",
        }
        live_df = live_df.rename(
            columns={k: v for k, v in rename_map.items() if k in live_df.columns}
        )

        # ── Step 2: resolve categoryid from category name (FIX 2) ────────────
        if "categoryid" not in live_df.columns:
            if "category" in live_df.columns:
                # Try to map display name → known ID
                live_df["categoryid"] = live_df["category"].map(
                    lambda name: str(_CATEGORY_NAME_TO_ID.get(str(name), 0))
                )
                # For names we couldn't resolve to an ID, pre-fill category_name
                # with the raw string so it survives enrich_dataframe().
                unresolved = live_df["categoryid"] == "0"
                if unresolved.any():
                    if "category_name" not in live_df.columns:
                        live_df["category_name"] = None
                    live_df.loc[unresolved, "category_name"] = live_df.loc[
                        unresolved, "category"
                    ]
            else:
                live_df["categoryid"] = "0"

        live_df["categoryid"] = live_df["categoryid"].astype(str)

        # Drop raw 'category' — enrich_dataframe() sets category_name from ID
        live_df = live_df.drop(columns=["category"], errors="ignore")

        # ── Step 3: fill required schema columns (FIX 3) ─────────────────────
        now = pd.Timestamp.now()

        def _csv_mode(col: str, fallback):
            """Use mode from CSV history; fall back to a sensible real-time value."""
            if not csv_df.empty and col in csv_df.columns:
                mode = csv_df[col].mode()
                if not mode.empty:
                    return mode.iloc[0]
            return fallback

        defaults: Dict[str, object] = {
            "action":         "view",
            "timestamp":      now,
            "day_of_week":    _csv_mode("day_of_week",    now.dayofweek),
            "week_of_month":  _csv_mode("week_of_month",  (now.day - 1) // 7 + 1),
            "hour_of_day":    now.hour,
            "item_available": 1,
            "is_weekend":     int(now.dayofweek >= 5),
            "itemid":         "unknown",
        }
        for col, default in defaults.items():
            if col not in live_df.columns:
                live_df[col] = default

        live_df["itemid"] = live_df["itemid"].astype(str)
        return live_df

    # ──────────────────────────────────────────────────────────────────────────
    # PRIVATE — core profile builder (shared by both public methods)
    # ──────────────────────────────────────────────────────────────────────────
    def _build_profile(self, user_id: str, user_df: pd.DataFrame) -> dict:
        """
        Build a rich behaviour profile from any DataFrame of user events.
        Called by observe() (CSV) and observe_from_events() (live/combined).
        """
        # ── Enrich with category names, slugs, departments ────────────────────
        # enrich_dataframe() (v2) adds: category_name, category_slug,
        # category_department.  If category_name is already set (e.g. from a
        # pre-filled unresolved live event), we preserve it after enrichment.
        pre_filled_names: Optional[pd.Series] = None
        if "category_name" in user_df.columns:
            pre_filled_names = user_df["category_name"].copy()

        user_df = enrich_dataframe(user_df)

        # Restore pre-filled names where enrich_dataframe left "Miscellaneous"
        if pre_filled_names is not None:
            mask = (user_df["category_name"] == _MISC_LABEL) & pre_filled_names.notna()
            user_df.loc[mask, "category_name"] = pre_filled_names[mask]

        total = len(user_df)

        # ── 1. Action funnel ──────────────────────────────────────────────────
        views     = len(user_df[user_df["action"] == "view"])
        carts     = len(user_df[user_df["action"] == "addtocart"])
        purchases = len(user_df[user_df["action"] == "transaction"])
        conversion_rate = round(purchases / total * 100, 2) if total else 0

        # ── 2. Category signals ───────────────────────────────────────────────
        # Filter "Miscellaneous" from every signal that feeds recommendations
        # or the user-facing profile text (FIX 5).
        known_df = user_df[user_df["category_name"] != _MISC_LABEL]
        misc_count = total - len(known_df)   # kept for diagnostic line in profile

        cat_counts    = known_df.groupby("category_name").size().sort_values(ascending=False)
        top_cat_names = dict(cat_counts.head(8))

        # FIX 1 — single aligned groupby keeps name + id on the same row,
        # so to_product_category() always receives a matched pair.
        top_cats = (
            known_df.groupby(["categoryid", "category_name"])
            .size()
            .reset_index(name="count")
            .sort_values("count", ascending=False)
            .head(5)
        )
        top_product_categories = list(dict.fromkeys([
            to_product_category(row["category_name"], row["categoryid"])
            for _, row in top_cats.iterrows()
        ]))[:3]

        intent_df = user_df[
            user_df["action"].isin(["addtocart", "transaction"]) &
            (user_df["category_name"] != _MISC_LABEL)
        ]
        intent_cat_names = intent_df["category_name"].value_counts().head(3).index.tolist()

        # ── 3. Department-level signals (new v2) ──────────────────────────────
        if "category_department" in user_df.columns:
            dept_counts = (
                known_df[known_df["category_department"] != "Other"]
                .groupby("category_department")
                .size()
                .sort_values(ascending=False)
            )
            top_departments = dept_counts.head(3).index.tolist()
        else:
            # Graceful fallback if running against old enrich_dataframe
            top_departments = list(dict.fromkeys([
                get_department(int(row["categoryid"]))
                for _, row in top_cats.iterrows()
                if str(row["categoryid"]).isdigit()
            ]))[:3]

        # ── 4. Item-level signals ─────────────────────────────────────────────
        item_counts     = user_df.groupby("itemid").size()
        repeat_items    = item_counts[item_counts > 1].head(5).index.tolist()
        purchased_items = user_df[user_df["action"] == "transaction"]["itemid"].tolist()
        carted_items    = set(user_df[user_df["action"] == "addtocart"]["itemid"].tolist())
        abandoned_items = list(carted_items - set(purchased_items))[:5]

        def item_label(iid: str) -> str:
            rows = user_df[user_df["itemid"] == iid]
            if rows.empty:
                return f"Item #{iid}"
            cat = rows["category_name"].iloc[0]
            return f"{cat} #{iid}"

        repeat_item_labels    = [item_label(i) for i in repeat_items]
        abandoned_item_labels = [item_label(i) for i in abandoned_items]
        unavailable_items     = (
            user_df[user_df["item_available"] == 0]["itemid"].unique().tolist()[:5]
        )
        unavailable_labels = [item_label(i) for i in unavailable_items]

        # ── 5. Temporal persona ───────────────────────────────────────────────
        is_weekend_pct = round(user_df["is_weekend"].mean() * 100, 1)
        peak_hours     = sorted(user_df["hour_of_day"].value_counts().head(3).index.tolist())
        day_map        = {
            0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday",
            4: "Friday",  5: "Saturday", 6: "Sunday",
        }
        active_days = [
            day_map.get(d, str(d))
            for d in user_df["day_of_week"].value_counts().head(3).index.tolist()
        ]
        recent_week = int(user_df.sort_values("timestamp")["week_of_month"].iloc[-1])

        # ── 6. Profile text ───────────────────────────────────────────────────
        misc_note = (
            f" ({misc_count:,} interactions in uncategorised items.)"
            if misc_count > 0 else ""
        )
        dept_line = (
            f"Top departments: {', '.join(top_departments)}."
            if top_departments else ""
        )

        profile_text = f"""
User {user_id} has {total:,} interactions ({views} views, {carts} add-to-carts, {purchases} purchases).
Conversion rate: {conversion_rate}%.{misc_note}

{dept_line}

Top browsed categories:
{', '.join([f"{name} ({count})" for name, count in list(top_cat_names.items())[:8]])}

Categories with strong purchase intent: {intent_cat_names if intent_cat_names else 'None'}

Items viewed repeatedly: {repeat_item_labels}
Abandoned cart items: {abandoned_item_labels}
Out-of-stock items user showed interest in: {unavailable_labels}

Behavioural patterns: {is_weekend_pct}% activity on weekends.
Most active on {active_days}. Peak hours: {peak_hours}.
Most recent activity: week {recent_week} of the month.
""".strip()

        # ── Store in ChromaDB (FIX 4 — now includes department + views/purchases)
        build_user_profile_v2(user_id, profile_text, {
            "total_events":         float(total),
            "views":                float(views),
            "purchases":            float(purchases),
            "conversion_rate":      float(conversion_rate),
            "top_category":         list(top_cat_names.keys())[0] if top_cat_names else "unknown",
            "top_product_category": top_product_categories[0] if top_product_categories else "tech",
            "top_department":       top_departments[0] if top_departments else "Other",
            "is_weekend_pct":       float(is_weekend_pct),
        })

        # ── Recent actions for UI ─────────────────────────────────────────────
        recent = user_df.sort_values("timestamp").tail(8).copy()
        base_cols = ["action", "category_name", "itemid", "item_available",
                     "hour_of_day", "is_weekend"]
        # Include v2 enrichment columns if present (safe to omit if using old map)
        extra_cols = [c for c in ["category_slug", "category_department"]
                      if c in recent.columns]
        recent_summary = recent[base_cols + extra_cols].to_dict("records")

        # ── Generate breadcrumbs for top categories ─────────────────────────
        # Use top_cats DataFrame (has actual categoryid), not top_cat_names dict
        # (which has category NAMES as keys — would cause int() conversion to fail)
        breadcrumbs = []
        for _, row in top_cats.iterrows():
            try:
                bc = get_breadcrumb(int(row["categoryid"]))
                if bc:
                    breadcrumbs.append(bc)
            except (ValueError, KeyError):
                pass

        return {
            "user_id":                user_id,
            "profile_summary":        profile_text,
            "recent_actions":         recent_summary,
            "total_events":           total,
            "purchased_items":        purchased_items[:6],
            "abandoned_items":        abandoned_items,
            "conversion_rate":        conversion_rate,
            "top_cat_names":          top_cat_names,
            "intent_names":           intent_cat_names,
            "top_product_categories": top_product_categories,
            "top_departments":        top_departments,          # new in v2
            "breadcrumbs":            breadcrumbs,              # new in v2
            "misc_event_count":       misc_count,              # diagnostic
            # ── 6 Signals for UI display ────────────────────────────────────
            "signal_purchases":       purchases,
            "signal_cart_abandons":   len(abandoned_items),
            "signal_repeat_items":    len(repeat_item_labels),
            "signal_categories":      list(top_cat_names.items())[:5],  # Top 5 with counts
            "signal_peak_hours":      peak_hours,
            "signal_active_days":     active_days,
            "signal_weekend_pct":     is_weekend_pct,
        }

    # ──────────────────────────────────────────────────────────────────────────
    # MODE 1 — Full CSV  (original signature preserved)
    # ──────────────────────────────────────────────────────────────────────────
    def observe(self, user_id: str) -> dict:
        """Read from full CSV — standard pipeline mode."""
        user_df = self.df[self.df["user_id"] == user_id].copy()
        if user_df.empty:
            raise ValueError(f"User '{user_id}' not found in events data.")
        return self._build_profile(user_id, user_df)

    # ──────────────────────────────────────────────────────────────────────────
    # MODE 2 — Live / Kafka streaming  (original signature preserved)
    # ──────────────────────────────────────────────────────────────────────────
    def observe_from_events(self, user_id: str, live_events: list) -> dict:
        """
        Build a profile from live streaming events (list of dicts).
        Works with simulated and real Kafka events.

        Blending rules
        ──────────────
        • 0 live events        → CSV history only
        • 1–4 live events      → live blended on top of CSV history
        • 5+ live events       → live only (CSV used only for column-fill defaults)

        All paths now go through _normalize_live_df() which resolves category
        names → IDs so enrich_dataframe() enriches live rows identically to
        CSV rows (FIX 2 + FIX 3).
        """
        csv_df = self.df[self.df["user_id"] == user_id].copy()

        # ── No live events at all → use CSV ──────────────────────────────────
        if not live_events:
            if csv_df.empty:
                raise ValueError(f"No data available for user '{user_id}'.")
            return self._build_profile(user_id, csv_df)

        # ── Normalise live events (applies FIX 2 + FIX 3) ───────────────────
        live_df = self._normalize_live_df(live_events, csv_df)

        # ── Decide blend strategy ─────────────────────────────────────────────
        if len(live_events) < 5 and not csv_df.empty:
            # Sparse live signal — enrich with CSV history for a richer profile
            combined = pd.concat([csv_df, live_df], ignore_index=True)
        else:
            # Sufficient live signal — live data drives the profile
            combined = live_df

        if combined.empty:
            raise ValueError(f"No data available for user '{user_id}'.")

        return self._build_profile(user_id, combined)



























# # agents/observer.py
# import os
# import pandas as pd
# from memory.vector_store import build_user_profile_v2
# from data.category_map import (
#     get_category_name,
#     get_category_names_list,
#     to_product_category,
#     enrich_dataframe,
#     print_mapping_coverage
# )


# class ObserverAgent:
#     def __init__(self, events_path=None):
#         if events_path is None:
#             base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#             events_path = os.path.join(base, "data", "user_events.csv")

#         self.df = pd.read_csv(events_path, parse_dates=["timestamp"])
#         self.df["categoryid"] = self.df["categoryid"].astype(str)
#         self.df["itemid"]     = self.df["itemid"].astype(str)

#     # ──────────────────────────────────────────────────────────────────────────
#     # CORE PROFILE BUILDER — shared by both observe() and observe_from_events()
#     # ──────────────────────────────────────────────────────────────────────────
#     def _build_profile(self, user_id: str, user_df: pd.DataFrame) -> dict:
#         """
#         Build a rich behaviour profile from any DataFrame of user events.
#         Called by both observe() (full CSV) and observe_from_events() (live data).
#         """
#         user_df = enrich_dataframe(user_df)
#         total   = len(user_df)

#         # ── 1. Action funnel ───────────────────────────────────────────────────
#         views     = len(user_df[user_df["action"] == "view"])
#         carts     = len(user_df[user_df["action"] == "addtocart"])
#         purchases = len(user_df[user_df["action"] == "transaction"])
#         conversion_rate = round(purchases / total * 100, 2) if total else 0

#         # ── 2. Category signals ────────────────────────────────────────────────
#         cat_counts    = user_df.groupby("category_name").size().sort_values(ascending=False)
#         top_cat_names = cat_counts.head(8).to_dict()

#         top_cat_ids = (
#             user_df.groupby("categoryid")
#             .size()
#             .sort_values(ascending=False)
#             .head(5)
#             .index.tolist()
#         )

#         top_product_categories = list(dict.fromkeys([
#             to_product_category(name, cid)
#             for name, cid in zip(list(top_cat_names.keys())[:5], top_cat_ids)
#         ]))[:3]

#         intent_df        = user_df[user_df["action"].isin(["addtocart", "transaction"])]
#         intent_cat_names = intent_df["category_name"].value_counts().head(3).index.tolist()

#         # ── 3. Item-level signals ──────────────────────────────────────────────
#         item_counts     = user_df.groupby("itemid").size()
#         repeat_items    = item_counts[item_counts > 1].head(5).index.tolist()
#         purchased_items = user_df[user_df["action"] == "transaction"]["itemid"].tolist()
#         carted_items    = set(user_df[user_df["action"] == "addtocart"]["itemid"].tolist())
#         abandoned_items = list(carted_items - set(purchased_items))[:5]

#         def item_label(iid: str) -> str:
#             rows = user_df[user_df["itemid"] == iid]
#             if rows.empty:
#                 return f"Item #{iid}"
#             cat = rows["category_name"].iloc[0]
#             return f"{cat} #{iid}"

#         repeat_item_labels    = [item_label(i) for i in repeat_items]
#         abandoned_item_labels = [item_label(i) for i in abandoned_items]
#         unavailable_items     = user_df[user_df["item_available"] == 0]["itemid"].unique().tolist()[:5]
#         unavailable_labels    = [item_label(i) for i in unavailable_items]

#         # ── 4. Temporal persona ────────────────────────────────────────────────
#         is_weekend_pct = round(user_df["is_weekend"].mean() * 100, 1)
#         peak_hours     = sorted(user_df["hour_of_day"].value_counts().head(3).index.tolist())
#         day_map        = {0:"Monday", 1:"Tuesday", 2:"Wednesday", 3:"Thursday",
#                           4:"Friday", 5:"Saturday", 6:"Sunday"}
#         active_days    = [
#             day_map.get(d, str(d))
#             for d in user_df["day_of_week"].value_counts().head(3).index.tolist()
#         ]
#         recent_week = int(user_df.sort_values("timestamp")["week_of_month"].iloc[-1])

#         # ── 5. Profile text ────────────────────────────────────────────────────
#         profile_text = f"""
# User {user_id} has {total:,} interactions ({views} views, {carts} add-to-carts, {purchases} purchases).
# Conversion rate: {conversion_rate}%.

# Top browsed categories:
# {', '.join([f"{name} ({count})" for name, count in list(top_cat_names.items())[:8]])}

# Categories with strong purchase intent: {intent_cat_names if intent_cat_names else 'None'}

# Items viewed repeatedly: {repeat_item_labels}
# Abandoned cart items: {abandoned_item_labels}
# Out-of-stock items user showed interest in: {unavailable_labels}

# Behavioural patterns: {is_weekend_pct}% activity on weekends.
# Most active on {active_days}. Peak hours: {peak_hours}.
# Most recent activity: week {recent_week} of the month.
# """.strip()

#         # ── Store in ChromaDB ──────────────────────────────────────────────────
#         build_user_profile_v2(user_id, profile_text, {
#             "total_events":         float(total),
#             "conversion_rate":      float(conversion_rate),
#             "top_category":         list(top_cat_names.keys())[0] if top_cat_names else "unknown",
#             "top_product_category": top_product_categories[0] if top_product_categories else "tech",
#             "is_weekend_pct":       float(is_weekend_pct),
#         })

#         # ── Recent actions for UI ──────────────────────────────────────────────
#         recent = user_df.sort_values("timestamp").tail(8).copy()
#         recent_summary = recent[[
#             "action", "category_name", "itemid",
#             "item_available", "hour_of_day", "is_weekend"
#         ]].to_dict("records")

#         return {
#             "user_id":                user_id,
#             "profile_summary":        profile_text,
#             "recent_actions":         recent_summary,
#             "total_events":           total,
#             "purchased_items":        purchased_items[:6],
#             "abandoned_items":        abandoned_items,
#             "conversion_rate":        conversion_rate,
#             "top_cat_names":          top_cat_names,
#             "intent_names":           intent_cat_names,
#             "top_product_categories": top_product_categories,
#         }

#     # ──────────────────────────────────────────────────────────────────────────
#     # MODE 1: Full CSV (original — unchanged)
#     # ──────────────────────────────────────────────────────────────────────────
#     def observe(self, user_id: str) -> dict:
#         """Read from full CSV — standard pipeline mode."""
#         user_df = self.df[self.df["user_id"] == user_id].copy()
#         if user_df.empty:
#             raise ValueError(f"User '{user_id}' not found in events data.")
#         return self._build_profile(user_id, user_df)

#     # ──────────────────────────────────────────────────────────────────────────
#     # MODE 2: Live streaming events (NEW — Kafka / simulated)
#     # ──────────────────────────────────────────────────────────────────────────
#     def observe_from_events(self, user_id: str, live_events: list) -> dict:
#         """
#         Build a profile from a list of live streaming events (dicts).
#         Used by the Live Feed tab — works with both simulated and real Kafka events.
#         Falls back to full CSV if live_events is too sparse (< 5 events).
#         """
#         if len(live_events) < 5:
#             # Not enough live data yet — enrich with CSV history
#             csv_df    = self.df[self.df["user_id"] == user_id].copy()
#             live_df   = pd.DataFrame(live_events) if live_events else pd.DataFrame()

#             if not live_df.empty:
#                 # Align live_df columns with CSV schema
#                 live_df = live_df.rename(columns={
#                     "category": "category_name",
#                     "item_id":  "itemid",
#                     "hour":     "hour_of_day",
#                     "available": "item_available",
#                 })
#                 # Fill missing columns with defaults from CSV or sensible values
#                 for col in ["categoryid", "day_of_week", "week_of_month"]:
#                     if col not in live_df.columns:
#                         if not csv_df.empty and col in csv_df.columns:
#                             live_df[col] = csv_df[col].iloc[0]
#                         else:
#                             live_df[col] = 0

#                 combined = pd.concat([csv_df, live_df], ignore_index=True)
#             else:
#                 combined = csv_df

#             if combined.empty:
#                 raise ValueError(f"No data available for user '{user_id}'.")
#             return self._build_profile(user_id, combined)

#         # Enough live events — build from live data only
#         live_df = pd.DataFrame(live_events)
#         live_df = live_df.rename(columns={
#             "category": "category_name",
#             "item_id":  "itemid",
#             "hour":     "hour_of_day",
#             "available": "item_available",
#         })

#         # Fill required columns
#         required_defaults = {
#             "categoryid":    "0",
#             "day_of_week":   0,
#             "week_of_month": 1,
#             "item_available": 1,
#             "is_weekend":    0,
#             "action":        "view",
#             "timestamp":     pd.Timestamp.now(),
#         }
#         for col, default in required_defaults.items():
#             if col not in live_df.columns:
#                 live_df[col] = default

#         return self._build_profile(user_id, live_df)