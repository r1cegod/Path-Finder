"""
Isolated test for job_graph.py
Goal: verify the search tool fires and the loop works.
NOT testing orchestrator — calling job_graph directly.
"""
from langchain_core.messages import HumanMessage
from backend.data.state import DEFAULT_STATE
from backend.job_graph import job_graph

config = {"configurable": {"thread_id": "job-test-1"}}

state = {
    **DEFAULT_STATE,
    "job_message": [
        HumanMessage(content="What are the salary ranges for AI engineers in Ho Chi Minh City?")
    ],
}

print("=== invoking job_graph ===")
result = job_graph.invoke(state, config)

print("\n--- job_message history ---")
for msg in result["job_message"]:
    print(f"[{type(msg).__name__}] {msg.content[:200]}")

print("\n--- job profile state ---")
print(result.get("job"))
