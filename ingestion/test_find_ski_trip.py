import io
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parent / "src"))
from find_ski_trip import Discovery, relevant  # noqa: E402


class DiscoveryTests(unittest.TestCase):
    def test_topic_requires_ski_and_school_or_family_phrase(self):
        self.assertTrue(relevant("Chapin ski trip"))
        self.assertTrue(relevant("Daddy-daughter skiing weekend"))
        self.assertFalse(relevant("Chapin school picnic"))
        self.assertFalse(relevant("Ski sale this weekend"))

    def test_decoded_body_and_promotion_exclusion(self):
        raw = (b"From example envelope\nSubject: Family trip\n"
               b"Content-Type: text/plain; charset=utf-8\n"
               b"Content-Transfer-Encoding: quoted-printable\n\nChapin ski=20trip")
        output = io.StringIO()
        finder = Discovery(io.BytesIO(raw), output)
        record = {"offset": 0, "length": len(raw), "decision": "excluded"}
        finder.write(json.dumps(record))
        self.assertEqual(finder.matches, 0)
        record["decision"] = "retained"
        finder.write(json.dumps(record))
        self.assertEqual(finder.matches, 1)
        self.assertIn("Chapin ski trip", json.loads(output.getvalue())["text"])


if __name__ == "__main__":
    unittest.main()
