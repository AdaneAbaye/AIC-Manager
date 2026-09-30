"""API tests: access code, rate limit, concurrency cap, error mapping and response redaction."""

import os
import unittest

try:
    from fastapi.testclient import TestClient

    import main
except ImportError:  # backend dependencies not installed locally
    main = None

FAKE_RESULT = {
    "approved_assets": [{"ticker": "JNJ", "pct": 100.0, "amount": 200.0, "rationale": "stable"}],
    "rejected_assets": [{"ticker": "XYZ", "reason": "too volatile"}],
    "agent_logs": [
        {"agent": "Scout", "lines": ["scan", "Outcome: ok"], "markdown": "key sk-abcdefghijklmnopqrstuvwxyz0123 leaked"}
    ],
    "raw_report": "| JNJ | 100% | $200 | stable |",
}
BODY = {"research_thesis": "stable growth", "budget": 200, "strategy": "monthly_dca"}


# In CI (GitHub sets CI=true) these tests must run, never silently skip.
@unittest.skipIf(main is None and not os.environ.get("CI"), "fastapi/crewai are not installed")
class TestApi(unittest.TestCase):
    def setUp(self):
        self._saved = (main.ACCESS_KEY, main.RATE_LIMIT_RUNS, main.run_research_session)
        main.ACCESS_KEY = ""
        main.RATE_LIMIT_RUNS = 100
        main._runs_by_client.clear()
        main.run_research_session = lambda **kw: FAKE_RESULT
        self.client = TestClient(main.app)

    def tearDown(self):
        main.ACCESS_KEY, main.RATE_LIMIT_RUNS, main.run_research_session = self._saved
        main._runs_by_client.clear()

    def test_health(self):
        self.assertEqual(self.client.get("/health").json(), {"status": "ok", "access_key_required": False})

    def test_access_code(self):
        main.ACCESS_KEY = "secret"
        self.assertTrue(self.client.get("/health").json()["access_key_required"])
        self.assertEqual(self.client.post("/api/research", json=BODY).status_code, 401)
        self.assertEqual(self.client.post("/api/research", json=BODY, headers={"X-Access-Key": "nope"}).status_code, 401)
        self.assertEqual(self.client.post("/api/research", json=BODY, headers={"X-Access-Key": "secret"}).status_code, 200)

    def test_rate_limit(self):
        main.RATE_LIMIT_RUNS = 2
        codes = [self.client.post("/api/research", json=BODY).status_code for _ in range(3)]
        self.assertEqual(codes, [200, 200, 429])

    def test_one_run_at_a_time(self):
        self.assertTrue(main._run_slots.acquire(blocking=False))
        try:
            self.assertEqual(self.client.post("/api/research", json=BODY).status_code, 429)
        finally:
            main._run_slots.release()
        self.assertEqual(self.client.post("/api/research", json=BODY).status_code, 200)

    def test_response_keeps_full_report_and_redacts_secrets(self):
        data = self.client.post("/api/research", json=BODY).json()
        md = data["agent_logs"][0]["markdown"]
        self.assertIn("leaked", md)
        self.assertNotIn("sk-abcdefghijklmnopqrstuvwxyz0123", md)

    def test_research_error_is_502_with_safe_message(self):
        def fail(**kw):
            raise main.ResearchSessionError("The AI service is busy right now.")

        main.run_research_session = fail
        res = self.client.post("/api/research", json=BODY)
        self.assertEqual(res.status_code, 502)
        self.assertIn("busy", res.json()["detail"])

    def test_input_bounds(self):
        self.assertEqual(self.client.post("/api/research", json={**BODY, "budget": 10**12}).status_code, 422)
        self.assertEqual(self.client.post("/api/research", json={**BODY, "research_thesis": ""}).status_code, 422)


if __name__ == "__main__":
    unittest.main()
