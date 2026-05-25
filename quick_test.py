from dotenv import load_dotenv
load_dotenv()

from agents.orchestrator_food import BehaviorIQOrchestrator

print("Testing Task B fix for user_00034...")
orch = BehaviorIQOrchestrator()

try:
    result = orch.task_b_get_recommendations("user_00034", 5)
    print("✅ Success!")
    print(f"   Recommendations: {len(result['recommendations'])}")
    print(f"   Strategy: {result['strategy']}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
