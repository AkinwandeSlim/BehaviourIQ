# app.py — BehaviorIQ Agent Dashboard
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import random
import os
from ui_helpers import (
    buying_stage_card, render_confidence_gauge, 
    render_conversion_triggers, match_score_bar, generic_recommendations,
)
from agents.orchestrator import run_agent
from data.category_map import get_category_name
from data.live_stream import (
    start_stream, stop_stream, is_running,
    get_stats, get_live_events, get_active_users,
)

try:
    from streamlit_autorefresh import st_autorefresh
    _AUTOREFRESH_AVAILABLE = True
except ImportError:
    _AUTOREFRESH_AVAILABLE = False

st.set_page_config(
    page_title="BehaviorIQ Agent",
    page_icon="🧠",
    layout="wide"
)


# ── Data loaders ──────────────────────────────────────────────────────────────

@st.cache_data(ttl=300)
def load_data():
    df = pd.read_csv("data/user_events.csv", parse_dates=["timestamp"])
    df["categoryid"] = df["categoryid"].astype(str)
    df["itemid"]     = df["itemid"].astype(str)
    from data.category_map import enrich_dataframe
    return enrich_dataframe(df)


@st.cache_data
def load_catalogue():
    path = os.path.join(os.path.dirname(__file__), "data", "products.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


df        = load_data()
catalogue = load_catalogue()
users     = sorted(df["user_id"].unique().tolist())




# ── Sidebar ───────────────────────────────────────────────────────────────────

st.sidebar.title("🧠 BehaviorIQ")
st.sidebar.markdown("*Predicts what you want before you ask*")
selected_user = st.sidebar.selectbox("Select User", users)

user_df   = df[df["user_id"] == selected_user].copy()
total     = len(user_df)
purchases = len(user_df[user_df["action"] == "transaction"])
conv_rate = round(purchases / total * 100, 1) if total > 0 else 0

st.sidebar.markdown("---")
st.sidebar.markdown("**Pipeline:**")
st.sidebar.markdown("1. 👁️ Observer — reads 6 behaviour signals")
st.sidebar.markdown("2. 🔮 Predictor — Claude infers buying stage")
st.sidebar.markdown("3. 🎯 Recommender — Claude + RAG + collab filtering")
st.sidebar.markdown("---")
st.sidebar.markdown("**Dataset:** 492 users · 70,239 events")
st.sidebar.markdown(f"**Selected:** `{selected_user}`")
st.sidebar.markdown(f"**Events:** {total} · **Conv. rate:** {conv_rate}%")


# ── Helper: display 6 observer signals in sidebar ─────────────────────────────
def render_observer_signals_sidebar(observation: dict):
    """Display the 6 observer signals that feed Claude."""
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Observer's 6 Signals")
    st.sidebar.markdown("*These feed the Predictor + Recommender*")
    
    # Signal 1: Confirmed Purchases
    purchases = observation.get("signal_purchases", 0)
    st.sidebar.metric(
        "✅ Confirmed Purchases",
        purchases,
        delta=None,
        delta_color="off"
    )
    
    # Signal 2: Cart Abandons (Frustrated Demand)
    abandons = observation.get("signal_cart_abandons", 0)
    st.sidebar.metric(
        "🛒 Cart Abandons",
        abandons,
        delta=None,
        delta_color="off"
    )
    
    # Signal 3: Repeat-Viewed Items
    repeat_items = observation.get("signal_repeat_items", 0)
    st.sidebar.metric(
        "👀 Repeat Views",
        repeat_items,
        delta=None,
        delta_color="off"
    )
    
    # Signal 4: Category Engagement (top 3)
    st.sidebar.markdown("**📁 Top Categories**")
    categories = observation.get("signal_categories", [])
    for cat_name, count in categories[:3]:
        st.sidebar.caption(f"• {cat_name}: {count} views")
    
    # Signal 5: Temporal Persona (Peak Hours)
    st.sidebar.markdown("**⏰ Peak Hours**")
    peak_hours = observation.get("signal_peak_hours", [])
    st.sidebar.caption(f"• Hours: {', '.join(map(str, peak_hours))}")
    
    # Signal 6: Temporal Persona (Active Days)
    st.sidebar.markdown("**📅 Active Days**")
    active_days = observation.get("signal_active_days", [])
    weekend_pct = observation.get("signal_weekend_pct", 0)
    st.sidebar.caption(f"• Days: {', '.join(active_days[:3])}")
    st.sidebar.caption(f"• Weekend: {weekend_pct:.1f}% of activity")


# ── Tabs ──────────────────────────────────────────────────────────────────────

tab_agent, tab_compare, tab_live = st.tabs([
    "🔮 Agent Dashboard", "⚖️ Before vs After", "🔴 Live Feed"
])


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — AGENT DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

with tab_agent:
    col_left, col_right = st.columns([1, 2])

    with col_left:
        st.subheader("📊 User Behaviour Profile")

        cat_counts = (
            user_df.groupby("category_name")
            .size()
            .sort_values(ascending=False)
            .head(8)
            .reset_index()
        )
        cat_counts.columns = ["category", "events"]

        fig_cat = px.bar(
            cat_counts, x="category", y="events",
            title="Category Engagement",
            color="events",
            color_continuous_scale="Blues"
        )
        fig_cat.update_layout(
            xaxis_tickangle=-35,
            showlegend=False,
            margin=dict(t=40, b=60),
            height=280
        )
        st.plotly_chart(fig_cat, use_container_width=True)

        views   = len(user_df[user_df["action"] == "view"])
        carts   = len(user_df[user_df["action"] == "addtocart"])
        unavail = len(user_df[user_df["item_available"] == 0])

        m1, m2, m3 = st.columns(3)
        m1.metric("Total Events", total)
        m2.metric("Purchases",    purchases)
        m3.metric("Add to Cart",  carts)

        m4, m5 = st.columns(2)
        m4.metric("Conversion Rate",   f"{conv_rate}%")
        m5.metric("Frustrated Demand", f"{unavail} events")

        top_cat = cat_counts.iloc[0]["category"] if len(cat_counts) > 0 else "—"
        st.info(f"🏆 Top category: **{top_cat}**")

        st.markdown("**🕐 Last 8 Actions**")
        recent = user_df.sort_values("timestamp").tail(8)[
            ["timestamp", "action", "category_name", "itemid", "item_available"]
        ].rename(columns={"category_name": "category"})
        st.dataframe(recent, use_container_width=True, hide_index=True)

    with col_right:
        st.subheader("🔮 BehaviorIQ Agent")

        if st.button("🚀 Run BehaviorIQ Agent", type="primary",
                     use_container_width=True, key="run_agent_tab1"):
            with st.spinner("Running pipeline…"):
                result = run_agent(selected_user)
            st.session_state["last_result"] = result
            st.session_state["last_user"]   = selected_user

        result = st.session_state.get("last_result")

        if result and st.session_state.get("last_user") == selected_user:

            if result.get("error"):
                st.error(f"❌ {result['error']}")

            else:
                obs    = result["observation"]
                pred   = result["prediction"]
                recs   = result["recommendations"]
                status = result.get("status", "complete")

                if status == "complete":
                    st.success("✅ Pipeline complete — Observer → Predictor → Recommender")
                    # Display 6 observer signals in sidebar for judges
                    render_observer_signals_sidebar(obs)
                else:
                    st.warning(f"⚠️ Pipeline status: {status}")

                st.markdown("---")
                st.markdown("### 🧠 Prediction")

                stage      = pred.get("buying_stage", "consideration")
                confidence = pred.get("confidence", 0.5)
                intent     = pred.get("predicted_intent", "")
                message    = pred.get("proactive_message", "")
                triggers   = pred.get("conversion_triggers", [])

                # ── Drift detection ───────────────────────────────────────
                try:
                    from agents.drift_detector import record_prediction, get_drift_history
                    drift_event = record_prediction(selected_user, pred)
                    if drift_event:
                        icon = "🚀" if drift_event["delta"] > 0 else "⚠️"
                        st.info(
                            f"{icon} **Concept Drift Detected** — "
                            f"{drift_event['message']}",
                        )
                    history = get_drift_history(selected_user)
                    if len(history) > 1:
                        with st.expander(
                            f"📈 Stage history for {selected_user} "
                            f"({len(history)} snapshots)"
                        ):
                            for snap in reversed(history):
                                st.write(
                                    f"`{snap['recorded_at'][:19]}` — "
                                    f"**{snap['buying_stage'].replace('_',' ').title()}** "
                                    f"({snap['confidence']:.0%})"
                                )
                except ImportError:
                    pass   # drift_detector not yet created — safe to skip

                buying_stage_card(stage, confidence)
                
                with st.expander("📊 Confidence Gauge", expanded=True):
                    render_confidence_gauge(confidence, height=180, key="confidence_gauge_dashboard")

                st.markdown(f"**Predicted Intent:** {intent}")

                if message:
                    # Extract trigger info from conversion_triggers if available
                    trigger_signal = ""
                    if triggers and len(triggers) > 0:
                        trigger_signal = triggers[0].get('signal', 'Recent activity')
                    
                    st.markdown(
                        f"<div style='background:#f0fdf4;border-left:5px solid #10b981;"
                        f"padding:12px 14px;border-radius:4px;margin:12px 0;'>"
                        f"<div style='font-weight:600;color:#047857;margin-bottom:4px;'>"
                        f"💬 Proactive Message for This Customer</div>"
                        f"<div style='font-size:0.95em;'><em>\"{message}\"</em></div>"
                        f"<div style='color:#6b7280;font-size:0.85em;margin-top:6px;'>"
                        f"🎯 Triggered by: <strong>{trigger_signal}</strong></div>"
                        f"</div>",
                        unsafe_allow_html=True
                    )

                # Display conversion triggers
                render_conversion_triggers(triggers)

                st.markdown("---")
                st.markdown("### 🎯 Personalised Recommendations")

                if not recs:
                    st.info("No recommendations returned — try running again.")
                else:
                    rec_cols = st.columns(len(recs))
                    for col, rec in zip(rec_cols, recs):
                        score = rec.get("match_score", 0.5)
                        with col:
                            with st.container(border=True):
                                st.markdown(f"**{rec.get('item_name','—')}**")
                                st.markdown(f"💰 **${rec.get('price', 0):.2f}**")
                                st.markdown(
                                    match_score_bar(score, "#27ae60"),
                                    unsafe_allow_html=True
                                )
                                st.caption(f"🧠 {rec.get('personalized_reason','')}")
                                st.button(
                                    rec.get("call_to_action", "Shop Now"),
                                    key=f"cta_{rec.get('item_id','')}",
                                    use_container_width=True
                                )

                    avg_score = sum(r.get("match_score", 0.5) for r in recs) / len(recs)
                    st.metric("Average Match Score", f"{int(avg_score * 100)}%")

                with st.expander("📋 Full Behaviour Profile (sent to Claude)"):
                    st.text(obs.get("profile_summary", ""))


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — BEFORE VS AFTER
# ═══════════════════════════════════════════════════════════════════════════════

with tab_compare:
    st.subheader("⚖️ Generic System vs BehaviorIQ")
    st.markdown("**Same user • Same moment • Two fundamentally different approaches**")

    if st.button("🚀 Run Comparison", type="primary",
                 use_container_width=True, key="run_agent_tab2"):
        with st.spinner("Running both systems..."):
            result = run_agent(selected_user)
        st.session_state["last_result"] = result
        st.session_state["last_user"]   = selected_user

    result      = st.session_state.get("last_result")
    active_user = st.session_state.get("last_user", selected_user)

    if result is None:
        st.info("👆 Click **Run Comparison** to evaluate both systems side by side.")

    elif result.get("error"):
        st.error(f"❌ {result['error']}")

    else:
        pred  = result.get("prediction", {})
        recs  = result.get("recommendations", [])
        obs   = result.get("observation", {})

        confidence_pct  = int(pred.get("confidence", 0.5) * 100)
        n_events        = obs.get("total_events", total)
        top_cat_display = list(obs.get("top_cat_names", {}).keys())
        top_cat_display = top_cat_display[0] if top_cat_display else "—"

        st.markdown(
            f"**User:** `{active_user}` &nbsp;|&nbsp; "
            f"**{n_events:,} events** &nbsp;|&nbsp; "
            f"**Top interest:** {top_cat_display}"
        )
        st.markdown("---")

        left, divider, right = st.columns([5, 0.25, 5])

        # ── Generic system ────────────────────────────────────────────────────
        with left:
            st.markdown(
                "<h3 style='color:#c0392b;'>❌ Generic System</h3>"
                "<p style='color:grey;font-size:0.85em;'>"
                "Popularity-based baseline (60% catalogue popularity + 40% price reasonableness)</p>",
                unsafe_allow_html=True
            )
            st.markdown(
                "<details><summary style='color:#7f8c8d;font-size:0.9em;cursor:pointer;'>"
                "📊 Scoring Formula</summary>"
                "<div style='background:#f8f9fa;padding:10px;border-radius:4px;margin-top:8px;'>"
                "<code>Score = (Item Popularity × 0.6) + (Price Reasonableness × 0.4)</code><br/>"
                "<small>• <b>Popularity</b>: How frequently item appears in catalogue<br/>"
                "• <b>Price Reasonableness</b>: Peak score $20-$200 (defensible mid-range)<br/>"
                "• <b>Result Range</b>: 0.30–0.65 (generic, no personalization)</small>"
                "</div></details>",
                unsafe_allow_html=True
            )
            user_seed    = hash(active_user) % 10000
            generic_recs = generic_recommendations(catalogue, n=4, seed=user_seed)
            generic_scores = [item.get("match_score", 0.42) for item in generic_recs]

            for item in generic_recs:
                score = item.get("match_score", 0.42)
                with st.container(border=True):
                    st.markdown(f"**🛍️ {item.get('name', 'Unknown Item')}**")
                    st.markdown(f"💰 ${item.get('price', 0):.2f}")
                    st.markdown(match_score_bar(score, "#e74c3c"), unsafe_allow_html=True)
                    st.caption("📋 Reason: Popular, reasonably-priced item")

            avg_generic = round(sum(generic_scores) / len(generic_scores), 2) if generic_scores else 0.42
            st.markdown("---")
            st.metric("📉 Avg. Relevance Score", f"{int(avg_generic * 100)}%")

        # ── Visual divider ────────────────────────────────────────────────────
        with divider:
            st.markdown(
                "<div style='border-left:3px solid #ddd;height:100%;"
                "min-height:520px;margin:auto;'></div>",
                unsafe_allow_html=True
            )

        # ── BehaviorIQ ────────────────────────────────────────────────────────
        with right:
            st.markdown(
                f"<h3 style='color:#27ae60;'>✅ BehaviorIQ ({confidence_pct}% confidence)</h3>"
                f"<p style='color:grey;font-size:0.85em;'>"
                f"Claude AI + {n_events:,} real events + RAG + collaborative filtering</p>",
                unsafe_allow_html=True
            )

            if recs:
                biq_scores = [rec.get("match_score", 0.78) for rec in recs]
                for rec in recs:
                    score = rec.get("match_score", 0.78)
                    with st.container(border=True):
                        st.markdown(f"**✨ {rec.get('item_name','—')}**")
                        st.markdown(f"💰 ${rec.get('price', 0):.2f}")
                        st.markdown(match_score_bar(score, "#27ae60"), unsafe_allow_html=True)
                        reason = rec.get("personalized_reason", "")
                        st.caption(f"🧠 {reason[:165]}{'...' if len(reason) > 165 else ''}")

                avg_biq = round(sum(biq_scores) / len(biq_scores), 2)
                st.markdown("---")
                st.metric(
                    "📈 Avg. Relevance Score",
                    f"{int(avg_biq * 100)}%",
                    delta=f"+{int((avg_biq - avg_generic) * 100)}pp vs generic"
                )
            else:
                st.info("No recommendations returned.")
                avg_biq = avg_generic

        # ── Lift summary ──────────────────────────────────────────────────────
        st.markdown("---")
        if recs:
            lift = int((avg_biq - avg_generic) * 100)
            st.markdown(
                f"<div style='background:#eafaf1;border-radius:10px;"
                f"padding:20px;text-align:center;'>"
                f"<h4>BehaviorIQ delivers "
                f"<span style='color:#27ae60;'>+{lift} percentage points</span> "
                f"higher relevance vs generic baseline</h4>"
                f"<p style='color:#555;margin:0;'><em>{pred.get('predicted_intent','')}</em></p>"
                f"</div>",
                unsafe_allow_html=True
            )

        # ── Score comparison chart ────────────────────────────────────────────
        if recs and generic_recs:
            st.markdown("#### 📊 Relevance Score Comparison")
            items_generic = [item.get("name", f"Item {i+1}") for i, item in enumerate(generic_recs)]
            items_biq     = [r.get("item_name", f"Rec {i+1}") for i, r in enumerate(recs)]

            fig = go.Figure()
            fig.add_trace(go.Bar(
                name="Generic System",
                x=items_generic[:4],
                y=generic_scores[:4],
                marker_color="#e74c3c"
            ))
            fig.add_trace(go.Bar(
                name="BehaviorIQ",
                x=items_biq[:4],
                y=[r.get("match_score", 0.8) for r in recs[:4]],
                marker_color="#27ae60"
            ))
            fig.update_layout(
                barmode="group",
                yaxis=dict(tickformat=".0%", range=[0, 1]),
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
                margin=dict(t=30, b=10),
                height=320
            )
            st.plotly_chart(fig, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — LIVE FEED
# ═══════════════════════════════════════════════════════════════════════════════

with tab_live:

    # ── Auto-refresh only when stream is running AND no agent job in flight ──
    _agent_running = st.session_state.get("live_agent_running", False)
    if _AUTOREFRESH_AVAILABLE and is_running() and not _agent_running:
        st_autorefresh(interval=3000, key="live_refresh")

    st.subheader("\U0001f534 Real-Time Event Stream")
    st.caption("Events replay from the 70,239-event RetailRocket dataset at ~2 events/second")

    ctrl1, ctrl2, ctrl3 = st.columns([1, 1, 2])

    with ctrl1:
        if not is_running():
            if st.button("\u25b6 Start Live Feed", type="primary", use_container_width=True):
                start_stream(delay=0.4, loop=True)
                st.rerun()
        else:
            if st.button("\u25a0 Stop", type="secondary", use_container_width=True):
                stop_stream()
                st.rerun()

    with ctrl2:
        live_user = st.selectbox(
            "Focus user",
            ["\u2014 All users \u2014"] + users,
            key="live_user_select"
        )

    with ctrl3:
        stats = get_stats()
        if stats["running"]:
            elapsed = (
                (pd.Timestamp.now() - pd.Timestamp(stats["started_at"])).seconds
                if stats["started_at"] else 0
            )
            st.markdown(
                "<div style='padding:8px;background:#eafaf1;border-radius:6px;'>"
                "\U0001f7e2 <b>LIVE</b> &nbsp;|&nbsp; "
                f"{stats['total_sent']:,} events streamed &nbsp;|&nbsp; "
                f"Uptime: {elapsed}s</div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                "<div style='padding:8px;background:#f8f9fa;border-radius:6px;'>"
                "\u26ab Stream stopped \u2014 click \u25b6 to start</div>",
                unsafe_allow_html=True
            )

    st.markdown("---")

    # Resolve focus user once — used by both columns
    live_focus = None if live_user == "\u2014 All users \u2014" else live_user

    # ← ADD THIS: clear stale result when user changes
    if live_focus != st.session_state.get("prev_live_focus"):
        st.session_state.pop("live_agent_result", None)
        st.session_state.pop("live_agent_error",  None)
        st.session_state["prev_live_focus"] = live_focus
    feed_col, agent_col = st.columns([1, 1])

    # ── Left: Event feed ──────────────────────────────────────────────────────
    with feed_col:
        st.markdown("#### \U0001f4e1 Incoming Events")
        events = get_live_events(user_id=live_focus, n=25)

        if events:
            ACTION_ICON = {"view": "\U0001f441", "addtocart": "\U0001f6d2", "transaction": "\U0001f4b3"}
            AVAIL_ICON  = {1: "\u2705", 0: "\u26d4"}
            rows = []
            for e in reversed(events):
                rows.append({
                    "Time":     e.get("stream_ts", "\u2014"),
                    "User":     e.get("user_id", "\u2014"),
                    "":         ACTION_ICON.get(e.get("action", ""), "\xb7"),
                    "Action":   e.get("action", "\u2014"),
                    "Category": str(e.get("category", "\u2014"))[:28],
                    "Avail":    AVAIL_ICON.get(int(e.get("available", 1)), "?"),
                    "\U0001f4b3": "\u2714" if e.get("has_purchase") else "",
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True,
                         hide_index=True, height=420)
            active = get_active_users(top_n=5)
            if active:
                st.markdown("**\U0001f525 Most active users in stream:**")
                st.markdown("  ".join([f"`{u}`" for u in active]))
        else:
            if not is_running():
                st.info("\U0001f446 Click **\u25b6 Start Live Feed** to begin streaming.")
            else:
                st.info("Waiting for events...")

    # ── Right: Agent on live data ─────────────────────────────────────────────
    with agent_col:
        st.markdown("#### \U0001f9e0 Agent on Live Data")

        if not live_focus:
            st.info("Select a specific user from **Focus user** above, "
                    "then click **Run Agent**.")
        else:
            live_events = get_live_events(user_id=live_focus, n=50)
            event_count = len(live_events)
            st.caption(
                f"**{live_focus}** \u2014 {event_count} live events buffered"
                + (" (+ full CSV history used for analysis)" if event_count < 5 else "")
            )

            col_run, col_clr = st.columns([3, 1])
            with col_run:
                run_live = st.button(
                    "\U0001f680 Run Agent on Live Data",
                    type="primary",
                    use_container_width=True,
                    key="live_agent_btn"
                )
            with col_clr:
                if st.button("\U0001f5d1", use_container_width=True,
                             key="live_clear_btn", help="Clear result"):
                    st.session_state.pop("live_agent_result", None)
                    st.session_state.pop("live_agent_error",  None)
                    st.rerun()

            if run_live:
                # Mark agent as running — pauses autorefresh interference
                st.session_state["live_agent_running"] = True
                st.session_state.pop("live_agent_result", None)
                st.session_state.pop("live_agent_error",  None)

                from agents.observer import ObserverAgent
                from agents.predictor import predict_user_needs
                from agents.recommender import generate_recommendations

                progress = st.empty()
                try:
                    progress.info("\U0001f441 Observer reading behaviour signals...")
                    observation = ObserverAgent().observe(live_focus)

                    progress.info("\U0001f9e0 Predictor analysing buying stage...")
                    prediction  = predict_user_needs(observation)

                    progress.info("\U0001f3af Recommender selecting products...")
                    recs = generate_recommendations(observation, prediction)

                    st.session_state["live_agent_result"] = {
                        "observation":     observation,
                        "prediction":      prediction,
                        "recommendations": recs,
                        "user_id":         live_focus,
                        "event_count":     event_count,
                    }
                    st.session_state["live_agent_error"]   = None
                    progress.success("✅ Pipeline complete!")
                    st.rerun()

                except Exception as e:
                    st.session_state["live_agent_error"]  = str(e)
                    st.session_state["live_agent_result"] = None
                    progress.error(f"❌ Agent error: {e}")
                    st.rerun()  # ← CRITICAL FIX: rerun even on error so display updates
                finally:
                    st.session_state["live_agent_running"] = False

            # ── Show persistent error if any ──────────────────────────────────
            live_error = st.session_state.get("live_agent_error")
            if live_error:
                st.error(f"\u274c Last agent error: {live_error}")

            # ── Show result ───────────────────────────────────────────────────
            live_result = st.session_state.get("live_agent_result")
            if (live_result
                    and live_result.get("user_id") == live_focus
                    and not live_error):

                pred = live_result["prediction"]
                recs = live_result["recommendations"]

                stage      = pred.get("buying_stage", "consideration")
                confidence = int(pred.get("confidence", 0.5) * 100)
                intent     = pred.get("predicted_intent", "")
                message    = pred.get("proactive_message", "")
                triggers   = pred.get("conversion_triggers", [])

                st.success(
                    f"\u2705 Pipeline complete \u2014 "
                    f"{live_result['event_count']} live events"
                )
                
                # Display 6 observer signals in sidebar for judges
                render_observer_signals_sidebar(live_result.get("observation", {}))

                buying_stage_card(stage, confidence / 100)
                
                with st.expander("📊 Confidence Gauge", expanded=True):
                    render_confidence_gauge(confidence / 100, height=160, key="confidence_gauge_live")

                st.markdown(f"**Intent:** {intent}")

                if message:
                    # Extract trigger info from conversion_triggers if available
                    trigger_signal = ""
                    if triggers and len(triggers) > 0:
                        trigger_signal = triggers[0].get('signal', 'Recent activity')
                    
                    st.markdown(
                        f"<div style='background:#f0fdf4;border-left:5px solid #10b981;"
                        f"padding:12px 14px;border-radius:4px;margin:12px 0;'>"
                        f"<div style='font-weight:600;color:#047857;margin-bottom:4px;'>"
                        f"💬 Proactive Message for This Customer</div>"
                        f"<div style='font-size:0.95em;'><em>\"{message}\"</em></div>"
                        f"<div style='color:#6b7280;font-size:0.85em;margin-top:6px;'>"
                        f"🎯 Triggered by: <strong>{trigger_signal}</strong></div>"
                        f"</div>",
                        unsafe_allow_html=True
                    )

                # Display conversion triggers with detective narrative
                render_conversion_triggers(triggers)

                if recs:
                    st.markdown("---")
                    st.markdown("### 🎯 Live Recommendations")
                    rec_cols = st.columns(len(recs))
                    for col, rec in zip(rec_cols, recs):
                        score = rec.get("match_score", 0.5)
                        with col:
                            with st.container(border=True):
                                st.markdown(f"**{rec.get('item_name','—')}**")
                                st.markdown(f"💰 **${rec.get('price', 0):.2f}**")
                                st.markdown(
                                    match_score_bar(score, "#27ae60"),
                                    unsafe_allow_html=True
                                )
                                st.caption(f"🧠 {rec.get('personalized_reason','')}")
                                st.button(
                                    rec.get("call_to_action", "Shop Now"),
                                    key=f"live_cta_{rec.get('item_id','')}",
                                    use_container_width=True
                                )
                    
                    avg_score = sum(r.get("match_score", 0.5) for r in recs) / len(recs)
                    st.metric("Average Match Score", f"{int(avg_score * 100)}%")

    st.markdown("---")
    st.markdown(
        "<div style='background:#f8f9fa;border-radius:8px;padding:12px 16px;"
        "font-size:0.85em;color:#555;'>"
        "\u2699\ufe0f <b>Architecture:</b> "
        "RetailRocket events \u2192 background thread \u2192 "
        "per-user buffer (50 events) \u2192 "
        "Observer (full CSV) \u2192 "
        "Claude Predictor + RAG Recommender \u2192 real-time recommendations. "
        "<br>For real Kafka: set <code>STREAM_MODE=kafka</code> in <code>.env</code> "
        "and run <code>python data/kafka_producer.py</code> in a second terminal."
        "</div>",
        unsafe_allow_html=True
    )