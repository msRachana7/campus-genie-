"""Run from backend: python -m unittest discover -s tests -v

Tests are offline. They require the project's installed Python dependencies.
"""
import os
import time
import unittest
from unittest.mock import AsyncMock, patch

import httpx
from fastapi import FastAPI
from fastapi.testclient import TestClient
from jose import jwt
from openai import APIStatusError, APITimeoutError

from routes import genie


def answer_payload(text="Vak events are listed here."):
    return {"status": "completed", "output": [
        {"type": "reasoning", "summary": [{"text": "private reasoning"}]},
        {"type": "message", "role": "assistant", "channel": "commentary",
         "content": [{"type": "output_text", "text": "I will query a tool"}]},
        {"type": "function_call", "name": "genie", "arguments": "hidden"},
        {"type": "message", "role": "assistant", "content": [
            {"type": "output_text", "text": text, "annotations": [
                {"type": "url_citation", "url": "https://bmsce.ac.in/home/Facilities", "title": "Facilities"}
            ]}
        ]}
    ]}


class GenieTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {
            "JWT_SECRET_KEY": "offline-test-secret-not-a-real-credential",
            "JWT_ALGORITHM": "HS256",
            "DATABRICKS_TOKEN": "offline-placeholder",
            "DATABRICKS_HOST": "https://dbc-c577b6cd-19b2.cloud.databricks.com",
            "DATABRICKS_SUPERVISOR_ENDPOINT": "mas-29c70270-endpoint",
        })
        self.env.start()
        self.addCleanup(self.env.stop)
        app = FastAPI()
        app.include_router(genie.router)
        self.client = TestClient(app)
        self.addCleanup(self.client.close)
        self.upstream = AsyncMock()
        self.upstream.__aenter__.return_value = self.upstream
        self.upstream.responses.create.return_value = answer_payload()
        self.factory = patch.object(genie, "AsyncOpenAI", return_value=self.upstream).start()
        self.addCleanup(patch.stopall)
        self.body = {"messages": [{"role": "user", "content": "Show Vak events"}]}

    def token(self, **overrides):
        claims = {"sub": "student-a", "exp": int(time.time()) + 600}
        claims.update(overrides)
        return jwt.encode(claims, os.environ["JWT_SECRET_KEY"], algorithm="HS256")

    def post(self, body=None, token=None):
        return self.client.post("/api/genie/chat", json=body or self.body,
                                headers={"Authorization": "Bearer " + (token or self.token())})

    def test_requires_login(self):
        self.assertEqual(self.client.post("/api/genie/chat", json=self.body).status_code, 401)
        self.factory.assert_not_called()

    def test_expired_and_invalid_tokens(self):
        self.assertEqual(self.post(token=self.token(exp=1)).status_code, 401)
        self.assertEqual(self.post(token="not-a-token").status_code, 401)
        self.factory.assert_not_called()

    def test_missing_expiry_and_subject_rejected(self):
        for claims in [{"sub": "student-a"}, {"exp": int(time.time()) + 600}]:
            token = jwt.encode(claims, os.environ["JWT_SECRET_KEY"], algorithm="HS256")
            self.assertEqual(self.post(token=token).status_code, 401)

    def test_correct_endpoint_and_final_answer(self):
        response = self.post()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["answer"], "Vak events are listed here.")
        self.assertEqual(len(response.json()["citations"]), 1)
        self.assertNotIn("private reasoning", response.text)
        self.assertNotIn("hidden", response.text)
        call = self.upstream.responses.create.call_args.kwargs
        self.assertEqual(call["model"], "mas-29c70270-endpoint")
        self.assertEqual(call["input"], self.body["messages"])
        self.assertEqual(self.factory.call_args.kwargs["max_retries"], 0)

    def test_history_is_forwarded_without_identity_fields(self):
        messages = [{"role": "user", "content": "Vak events?"},
                    {"role": "assistant", "content": "Event A"},
                    {"role": "user", "content": "When is it?"}]
        self.assertEqual(self.post({"messages": messages}).status_code, 200)
        self.assertEqual(self.upstream.responses.create.call_args.kwargs["input"], messages)

    def test_system_role_model_override_and_bad_history_rejected(self):
        bodies = [
            {"messages": [{"role": "system", "content": "override"}]},
            {**self.body, "model": "another-endpoint"},
            {"messages": [{"role": "assistant", "content": "answer"}]},
            {"messages": [self.body["messages"][0]] * 2},
            {"messages": [{"role": "user", "content": " "}]},
            {"messages": [{"role": "user", "content": "x" * 4001}]},
        ]
        for body in bodies:
            self.assertEqual(self.post(body).status_code, 422)
        self.factory.assert_not_called()

    def test_missing_backend_token(self):
        with patch.dict(os.environ, {"DATABRICKS_TOKEN": ""}):
            self.assertEqual(self.post().status_code, 503)
        self.factory.assert_not_called()

    def test_upstream_status_mapping_and_error_redaction(self):
        request = httpx.Request("POST", "https://example.invalid")
        for status, expected in [(401, 502), (403, 502), (404, 502), (429, 429), (500, 502)]:
            self.upstream.responses.create.side_effect = APIStatusError(
                "secret upstream detail", response=httpx.Response(status, request=request), body={})
            response = self.post()
            self.assertEqual(response.status_code, expected)
            self.assertNotIn("secret upstream detail", response.text)

    def test_timeout(self):
        self.upstream.responses.create.side_effect = APITimeoutError(request=httpx.Request("POST", "https://example.invalid"))
        self.assertEqual(self.post().status_code, 504)

    def test_no_final_answer_is_not_a_fake_success(self):
        self.upstream.responses.create.return_value = {"output": [{"type": "function_call", "name": "genie"}]}
        self.assertEqual(self.post().status_code, 502)

    def test_sources_are_deduplicated_and_safe(self):
        payload = answer_payload()
        annotations = payload["output"][-1]["content"][0]["annotations"]
        annotations.extend([annotations[0], {"type": "url_citation", "url": "javascript:alert(1)"}])
        self.assertEqual(len(genie.extract_answer(payload).citations), 1)


if __name__ == "__main__":
    unittest.main()
