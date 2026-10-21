import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fastapi.testclient import TestClient

from entourage_server.app import create_app
from entourage_server.config import Settings


class FoundationTests(unittest.TestCase):
    def test_liveness_does_not_claim_unimplemented_features_or_leak_config(self):
        with TemporaryDirectory() as directory, TestClient(create_app(Settings(
            ollama_upstream="https://private-mac.example", database_path=Path(directory) / "test.db",
        ))) as client:
            response = client.get("/api/v1/health")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {
                "status": "ok", "api_version": "v1", "stage": "persistence",
                "execution_enabled": False, "model": None,
                "capabilities": ["conversations", "history_import", "queued_turns"],
            })
            self.assertNotIn("private-mac", response.text)
            self.assertEqual(client.put("/api/v1/conversations/test/turns/test", json={}).status_code, 422)
            self.assertEqual(client.get("/api/jobs/test").status_code, 404)
            self.assertIn("/api/v1/health", client.get("/openapi.json").json()["paths"])

    def test_configuration_defaults_and_remote_override(self):
        with patch.dict("os.environ", {}, clear=True), patch("entourage_server.config.Path.exists", return_value=False):
            self.assertEqual(Settings.from_environment(), Settings())
        with patch.dict("os.environ", {
            "ENTOURAGE_OLLAMA_UPSTREAM": "https://mac.example:443",
            "ENTOURAGE_MODEL": "another-model",
            "ENTOURAGE_DATABASE_PATH": "custom/agent.sqlite3",
        }, clear=True):
            settings = Settings.from_environment()
            self.assertEqual(settings.ollama_upstream, "https://mac.example:443")
            self.assertEqual(settings.model, "another-model")
            self.assertEqual(settings.database_path, Path("custom/agent.sqlite3"))

    def test_invalid_upstreams_fail_at_startup(self):
        for url in ["file:///tmp/model", "http://", "http://user:secret@mac",
                    "http://mac/llm", "http://mac?secret", "http://mac#fragment",
                    "http://mac:99999", "http://mac:0", "http://mac:invalid"]:
            with self.subTest(url=url), self.assertRaises(ValueError):
                Settings(ollama_upstream=url)
        with self.assertRaises(ValueError):
            Settings(model=" ")

    def test_inference_limits_are_configurable_and_validated(self):
        with patch.dict("os.environ", {"ENTOURAGE_CONTEXT_TOKENS": "16384", "ENTOURAGE_MAX_OUTPUT_TOKENS": "2048"}, clear=True):
            settings = Settings.from_environment()
            self.assertEqual((settings.context_tokens, settings.max_output_tokens), (16384, 2048))
        for args in [{"context_tokens": 0}, {"context_tokens": True}, {"context_tokens": 262145},
                     {"max_output_tokens": 0}, {"max_output_tokens": -1},
                     {"context_tokens": 4096, "max_output_tokens": 4096}]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                Settings(**args)
        with patch.dict("os.environ", {"ENTOURAGE_CONTEXT_TOKENS": "not-a-number"}, clear=True):
            with self.assertRaises(ValueError):
                Settings.from_environment()

    def test_session_gap_is_configurable_and_validated(self):
        with patch.dict("os.environ", {"ENTOURAGE_CONTEXT_SESSION_GAP_MINUTES": "120"}, clear=True):
            self.assertEqual(Settings.from_environment().context_session_gap_minutes, 120)
        for gap in [0, -1, True, 1.5, 1441]:
            with self.subTest(gap=gap), self.assertRaises(ValueError):
                Settings(context_session_gap_minutes=gap)


if __name__ == "__main__":
    unittest.main()
