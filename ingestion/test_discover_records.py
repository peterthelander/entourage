import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).parent / "src"))
from catalog_mail import run as catalog
from discover_records import run


class DiscoveryTests(unittest.TestCase):
    def test_selection_budgets_and_source_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "mail.mbox"
            source.write_bytes(b"".join(
                b"From sender\nDate: Sun, 10 Nov 2024 12:00:00 +0000\nSubject: Hotel booking\nX-Gmail-Labels: " + label + b"\n\nHotel stay June 4-6, 2025.\n"
                for label in [b"Inbox", b"Category Promotions", b"Sent"]))
            catalog([source], root / "catalog", max_bytes=10000)
            rules = root / "rules.json"
            rules.write_text(json.dumps({"rules": [{"name": "lodging", "any_terms": ["hotel"]}]}))
            report = run([root / "catalog"], rules, root / "leads", max_records=1)
            self.assertEqual(report["counts"]["normalized"], 1)
            self.assertEqual(report["counts"]["discovery_budget"], 1)
            self.assertEqual(report["counts"]["excluded_or_oversized_headers"], 1)
            record = json.loads((root / "leads/records.jsonl").read_text())
            self.assertEqual(record["discovery"]["membership"], "unreviewed_lead")
            source.write_bytes(source.read_bytes() + b"Changed")
            with self.assertRaises(ValueError):
                run([root / "catalog"], rules, root / "changed")


if __name__ == "__main__":
    unittest.main()
