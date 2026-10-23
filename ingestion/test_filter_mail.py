import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("filter_mail", Path(__file__).parent / "src/filter_mail.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class FilterTests(unittest.TestCase):
    def test_labels_offsets_and_partial_sample(self):
        messages = [
            b'From a@example.com Sat Jan 1 00:00:00 2022\nX-Gmail-Labels: Inbox,\n Category Promotions\nMessage-ID: <a>\n\nbody\n',
            b'From b@example.com Sat Jan 1 00:00:00 2022\nX-Gmail-Labels: "Custom, label",Category Promotions Extra\n\n>From quoted body\n',
            b'From c@example.com Sat Jan 1 00:00:00 2022\nSubject: no labels\n\nlast\n',
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.mbox"
            path.write_bytes(b"".join(messages))
            manifest = io.StringIO()
            report = module.scan(path, path.stat().st_size, manifest)
            self.assertEqual(report["excluded_messages"], 1)
            self.assertEqual(report["excluded_bytes"], len(messages[0]))
            self.assertEqual(report["retained_bytes"], sum(map(len, messages[1:])))
            self.assertEqual(report["messages_without_labels"], 1)
            rows = [json.loads(line) for line in manifest.getvalue().splitlines()]
            self.assertEqual(rows[1]["offset"], len(messages[0]))
            self.assertIn("Custom, label", rows[1]["labels"])
            partial = module.scan(path, len(messages[0]) + 20)
            self.assertEqual(partial["excluded_messages"], 1)
            self.assertEqual(partial["retained_messages"], 0)
            self.assertEqual(partial["trailing_partial_bytes_not_counted"], 20)


if __name__ == "__main__":
    unittest.main()
