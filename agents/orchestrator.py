# agents/orchestrator.py
from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional
from agents.observer import ObserverAgent
from agents.predictor import predict_user_needs
from agents.recommender import generate_recommendations


# ── State schema ───────────────────────────────────────────────────────────
class AgentState(TypedDict):
    user_id:         str
    observation:     dict
    prediction:      dict
    recommendations: list
    error:           Optional[str]
    status:          str          # starting | observed | predicted | complete | failed


# ── Observer instantiated once — CSV loaded at startup, not on every run ──
observer = ObserverAgent()


# ── Node 1: Observe ────────────────────────────────────────────────────────
def observe_node(state: AgentState) -> AgentState:
    """
    Reads raw events for user_id from the dataset.
    Extracts 6 behavioural signals:
      - confirmed purchases, cart abandons, repeat views,
        frustrated demand, temporal persona, category engagement
    Stores embedding in ChromaDB.
    """
    try:
        obs = observer.observe(state["user_id"])
        return {
            **state,
            "observation": obs,
            "status":      "observed"
        }
    except ValueError as e:
        # User not found in dataset
        return {
            **state,
            "error":  f"User '{state['user_id']}' not found in dataset: {str(e)}",
            "status": "failed"
        }
    except Exception as e:
        return {
            **state,
            "error":  f"Observer failed: {str(e)}",
            "status": "failed"
        }


# ── Node 2: Predict ────────────────────────────────────────────────────────
def predict_node(state: AgentState) -> AgentState:
    """
    Sends rich behaviour profile to Claude.
    Returns:
      - predicted_intent    : what the customer is about to buy
      - buying_stage        : awareness | consideration | ready_to_buy | repeat_buyer
      - confidence          : 0.0–1.0 signal strength
      - conversion_triggers : 3 specific behaviour signals + interpretations + actions
      - proactive_message   : personalised nudge for this user
    """
    if state.get("error"):
        return state
    try:
        pred = predict_user_needs(state["observation"])
        return {
            **state,
            "prediction": pred,
            "status":     "predicted"
        }
    except Exception as e:
        return {
            **state,
            "error":  f"Predictor failed: {str(e)}",
            "status": "failed"
        }


# ── Node 3: Recommend ──────────────────────────────────────────────────────
def recommend_node(state: AgentState) -> AgentState:
    """
    Combines behaviour profile + prediction + collaborative filtering signal
    to generate top 4 personalised product recommendations.
    Collaborative filtering: fetches 3 nearest-neighbour user profiles
    from ChromaDB and passes their purchase patterns to Claude.
    """
    if state.get("error"):
        return state
    try:
        recs = generate_recommendations(
            state["observation"],
            state["prediction"]
        )
        return {
            **state,
            "recommendations": recs,
            "status":          "complete"
        }
    except Exception as e:
        return {
            **state,
            "error":  f"Recommender failed: {str(e)}",
            "status": "failed"
        }


# ── Build LangGraph pipeline ───────────────────────────────────────────────
workflow = StateGraph(AgentState)

workflow.add_node("observe",   observe_node)
workflow.add_node("predict",   predict_node)
workflow.add_node("recommend", recommend_node)

workflow.set_entry_point("observe")
workflow.add_edge("observe",   "predict")
workflow.add_edge("predict",   "recommend")
workflow.add_edge("recommend", END)

agent = workflow.compile()


# ── Public entry point ─────────────────────────────────────────────────────
def run_agent(user_id: str) -> AgentState:
    """
    Run the full BehaviorIQ pipeline for a given user.

    Returns AgentState with:
      state["observation"]     — rich behaviour profile + all 6 signals
      state["prediction"]      — buying stage, intent, confidence, triggers
      state["recommendations"] — top 4 personalised products
      state["status"]          — observed | predicted | complete | failed
      state["error"]           — None if successful, error message if failed
    """
    return agent.invoke({
        "user_id":         user_id,
        "observation":     {},
        "prediction":      {},
        "recommendations": [],
        "error":           None,
        "status":          "starting"
    })