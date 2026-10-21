from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from fastapi.testclient import TestClient

from entourage_server.app import create_app
from entourage_server.config import Settings


class SeamlessAccessTests(unittest.TestCase):
    def test_private_owner_and_direct_local_access_without_token(self):
        with TemporaryDirectory() as directory:
            settings = Settings(database_path=Path(directory) / "test.db", api_token="diagnostic-only-token" * 2,
                                trust_local=True, tailscale_login="owner@example.com",
                                allowed_origins=("http://localhost:8081", "https://hp.example.ts.net"))
            with TestClient(create_app(settings), client=("127.0.0.1", 1234)) as client:
                self.assertEqual(client.get("/api/v1/conversations", headers={"Host": "localhost:8000", "Origin": "http://localhost:8081"}).status_code, 200)
                proxy = {"Host": "hp.example.ts.net", "Tailscale-User-Login": "owner@example.com", "X-Forwarded-For": "100.64.0.2"}
                self.assertEqual(client.get("/api/v1/conversations", headers=proxy).status_code, 200)
                self.assertEqual(client.get("/api/v1/conversations", headers={**proxy, "Tailscale-User-Login": "another@example.com"}).status_code, 401)
                self.assertEqual(client.get("/api/v1/conversations", headers={"Host": "hp.example.ts.net"}).status_code, 401)
                self.assertEqual(client.get("/api/v1/conversations", headers={"Host": "localhost:8000", "X-Forwarded-For": "100.64.0.2"}).status_code, 401)
                self.assertEqual(client.get("/api/v1/conversations", headers={**proxy, "Origin": "https://attacker.example"}).status_code, 403)
            with TestClient(create_app(settings), client=("100.64.0.2", 1234)) as direct_network:
                self.assertEqual(direct_network.get("/api/v1/conversations", headers=proxy).status_code, 401)
