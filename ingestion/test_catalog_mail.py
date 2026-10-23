import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).parent / "src"))
from catalog_mail import headers, ranges, run


class CatalogTests(unittest.TestCase):
    def test_boundaries_across_blocks_and_partial_tail(self):
        messages = [b"From sender\nDate: Sat, 7 Feb 2026 12:00:00 +0000\nSubject: Hello\n\nBody\n",
                    b"From sender\r\nSubject: Other\r\n\r\n>From escaped body\r\n"]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mail.mbox"
            path.write_bytes(b"".join(messages))
            for block_size in range(8, 40):
                self.assertEqual(list(ranges(path, max_bytes=1000, block_size=block_size)),
                                 [(0, len(messages[0])), (len(messages[0]), len(messages[1]))])
            self.assertEqual(list(ranges(path, max_bytes=len(messages[0]) + 8)), [(0, len(messages[0]))])
            self.assertEqual(list(ranges(path, max_bytes=1000, start_offset=len(messages[0]))),
                             [(len(messages[0]), len(messages[1]))])

    def test_header_filter_and_catalog_coverage(self):
        raw = b'From sender\r\nDate: Sat, 7 Feb 2026 12:00:00 +0000\r\nX-Gmail-Labels: Inbox,"Category Promotions"\r\nSubject: Offer\r\n\r\nPrivate body\r\n'
        self.assertTrue(headers(io.BytesIO(raw), 0, len(raw))["excluded"])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mail.mbox"
            path.write_bytes(raw)
            output = Path(tmp) / "catalog"
            report = run([path], output, max_bytes=10000)
            self.assertTrue(report["sources"][0]["complete_file"])
            self.assertEqual(report["sources"][0]["excluded_promotions"], 1)
            self.assertNotIn("Private body", (output / "headers.jsonl").read_text())
            self.assertEqual(json.loads((output / "headers.jsonl").read_text())["observed_at"], "2026-02-07T12:00:00+00:00")


if __name__ == "__main__":
    unittest.main()
