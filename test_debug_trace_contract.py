import os
import tempfile
import unittest
import uuid
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("OPENAI_API_KEY", "test-key")

from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage, HumanMessage

import main
from backend.debug_trace import (
    LiveTraceCollector,
    is_trace_active,
    start_trace_session,
    stop_trace_session,
)


class FakeGraph:
    def __init__(self):
        self.values = {}
        self.last_patch = None

    async def aget_state(self, _config):
        return SimpleNamespace(values=self.values)

    async def aupdate_state(self, _config, patch, as_node=None):
        self.last_patch = patch
        self.last_as_node = as_node
        self.values.update(patch)


class DebugTraceContractTest(unittest.TestCase):
    def test_debug_endpoints_return_404_when_disabled(self):
        old_value = os.environ.pop("PATHFINDER_DEBUG", None)
        try:
            client = TestClient(main.app)
            response = client.get("/debug/state/session-a")
        finally:
            if old_value is not None:
                os.environ["PATHFINDER_DEBUG"] = old_value

        self.assertEqual(response.status_code, 404)

    def test_debug_state_patch_returns_raw_and_frontend_state(self):
        old_graph = main.input_orchestrator
        os.environ["PATHFINDER_DEBUG"] = "1"
        fake_graph = FakeGraph()
        main.input_orchestrator = fake_graph
        try:
            client = TestClient(main.app)
            response = client.post(
                "/debug/state/session-b",
                json={
                    "patch": {
                        "stage": {"current_stage": "university"},
                        "university": {"done": True},
                        "messages": [{"role": "user", "content": "hello"}],
                    }
                },
            )
        finally:
            main.input_orchestrator = old_graph

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["frontendState"]["currentStage"], "uni")
        self.assertEqual(payload["frontendState"]["completedStages"], ["uni"])
        self.assertEqual(fake_graph.last_as_node, main.CHECKPOINT_PATCH_NODE)
        self.assertIsInstance(fake_graph.last_patch["messages"][0], HumanMessage)

    def test_test_endpoint_merges_mi_and_riasec_for_same_session(self):
        client = TestClient(main.app)
        session_id = f"thinking-test-{uuid.uuid4()}"

        mi_response = client.post(
            f"/test/{session_id}",
            json={"brain_type": ["logical", "kinesthetic"]},
        )
        riasec_response = client.post(
            f"/test/{session_id}",
            json={"riasec_top": ["I", "R"]},
        )

        self.assertEqual(mi_response.status_code, 200)
        self.assertEqual(riasec_response.status_code, 200)

        snapshot = main.input_orchestrator.get_state(
            {"configurable": {"thread_id": session_id}}
        )
        thinking = snapshot.values.get("thinking")
        self.assertEqual(thinking["brain_type"], ["logical", "kinesthetic"])
        self.assertEqual(thinking["riasec_top"], ["I", "R"])
        self.assertFalse(thinking["done"])
        for field_name in [
            "learning_mode",
            "env_constraint",
            "social_battery",
            "personality_type",
        ]:
            self.assertEqual(thinking[field_name], {"content": "not yet", "confidence": 0.0})

    def test_test_endpoint_marks_empty_mi_submission_complete(self):
        client = TestClient(main.app)
        session_id = f"empty-mi-test-{uuid.uuid4()}"

        response = client.post(f"/test/{session_id}", json={"brain_type": []})

        self.assertEqual(response.status_code, 200)
        self.assertIn('"miSubmitted": true', response.text)
        snapshot = main.input_orchestrator.get_state(
            {"configurable": {"thread_id": session_id}}
        )
        self.assertEqual(snapshot.values["thinking"]["brain_type"], [])

    def test_trace_start_stop_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            threads_dir = Path(tmp)
            started = start_trace_session("session-c", threads_dir=threads_dir)

            self.assertTrue(started["active"])
            self.assertTrue(is_trace_active("session-c", threads_dir=threads_dir))

            stopped = stop_trace_session("session-c", threads_dir=threads_dir)

            self.assertFalse(stopped["active"])
            self.assertFalse(is_trace_active("session-c", threads_dir=threads_dir))

    def test_live_trace_writer_uses_approx_token_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            threads_dir = Path(tmp)
            start_trace_session("session-d", threads_dir=threads_dir)
            collector = LiveTraceCollector(
                session_id="session-d",
                user_message="hello",
                threads_dir=threads_dir,
            )
            collector.add_event(
                {
                    "event": "on_chat_model_start",
                    "name": "ChatOpenAI",
                    "run_id": "run-1",
                    "metadata": {"langgraph_node": "input_parser"},
                    "data": {"input": [HumanMessage(content="hello")]},
                }
            )
            collector.add_event(
                {
                    "event": "on_chat_model_end",
                    "name": "ChatOpenAI",
                    "run_id": "run-1",
                    "metadata": {"langgraph_node": "input_parser"},
                    "data": {"output": AIMessage(content="ok")},
                }
            )

            path = collector.write(
                status="success",
                output_state={"messages": [AIMessage(content="ok")]},
                frontend_state={"currentStage": "thinking"},
            )

            self.assertTrue(path.exists())
            payload = path.read_text(encoding="utf-8")
            self.assertIn('"source": "approx"', payload)
            self.assertIn('"trace_source": "frontend_live"', payload)


if __name__ == "__main__":
    unittest.main()
