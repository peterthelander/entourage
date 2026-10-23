import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent / "src"))
from local_model import complete, completed_content, load_config  # noqa: E402


class LocalModelTests(unittest.TestCase):
    def test_completed_content_rejects_truncation_and_tools(self):
        for finish, message in (("length", {"content": "cut"}), ("stop", {"content": "text", "tool_calls": [{}]}), ("stop", {"content": None})):
            with self.assertRaises(ValueError):
                completed_content({"choices": [{"finish_reason": finish, "message": message}]})
        self.assertEqual(completed_content({"choices": [{"finish_reason": "stop", "message": {"content": "{}"}}]}), "{}")

    def test_bounded_response_saved_before_parsing(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "response.json"
            response = SimpleNamespace(raise_for_status=lambda: None, iter_bytes=lambda: iter([b'{"test":true}']))
            client = MagicMock()
            client.stream.return_value.__enter__.return_value = response
            self.assertEqual(complete(client, "http://localhost:8080", {}, path), {"test": True})
            self.assertEqual(path.read_bytes(), b'{"test":true}')
            response.iter_bytes = lambda: iter([b"x" * (2 * 1024 * 1024 + 1)])
            with self.assertRaises(ValueError):
                complete(client, "http://localhost:8080", {}, Path(directory) / "too-large.json")

    def test_no_hosted_fallback_and_no_credentials_in_origin(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            for provider, origin in (("gemini", "http://localhost"), ("llama_cpp", "http://secret@localhost")):
                path.write_text(json.dumps({"ENTOURAGE_INFERENCE_PROVIDER": provider, "ENTOURAGE_LLAMA_CPP_UPSTREAM": origin, "ENTOURAGE_MODEL": "synthetic"}))
                with self.assertRaises(ValueError):
                    load_config(path)
