from email.message import EmailMessage
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).parent / "src"))
from memory_candidates import render  # noqa: E402
from normalize_mail import Normalizer, normalize, run  # noqa: E402


def mail(text="Please bring a book.", date="Tue, 01 Apr 2025 10:00:00 -0400"):
    message = EmailMessage()
    message["Date"] = date
    message["Subject"] = "Book group"
    message["Message-ID"] = "<synthetic@example.test>"
    message.set_content(text)
    return message


def mbox(message):
    return b"From synthetic@example.test Tue Apr 1 10:00:00 2025\n" + message.as_bytes()


class MailNormalizerTests(unittest.TestCase):
    def test_provenance_dates_and_body_alternatives(self):
        message = mail()
        message.add_alternative("<p>Duplicate HTML version</p>", subtype="html")
        raw = mbox(message)
        record, reason = normalize(raw, Path("synthetic.mbox"), 50)
        self.assertIsNone(reason)
        self.assertEqual(record["text"], "Please bring a book.")
        self.assertEqual(record["observed_at"], "2025-04-01T10:00:00-04:00")
        self.assertIsNone(record["event_date"])
        self.assertEqual(record["source"]["sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(record["source"]["locator"], f"mbox offset=50 length={len(raw)}")
        self.assertEqual(record["id"], normalize(raw, Path("elsewhere.mbox"), 0)[0]["id"])
        self.assertIn("journals/2025-04-01.md", render([record], {"version": 1, "articles": []}))

    def test_html_and_attached_forward_are_separate(self):
        message = mail("<html><head><title>hidden</title></head><body><p>Reading &amp; books</p><script>secret()</script></body></html>")
        message.set_type("text/html")
        message.add_attachment(mail("Do not import this attached forward."))
        record, _ = normalize(mbox(message), Path("synthetic.mbox"), 0)
        self.assertEqual(record["text"], "Reading & books")
        self.assertNotIn("secret", record["text"])
        self.assertFalse(record["extraction"]["attachments_included"])
        self.assertTrue(record["extraction"]["omitted_parts"])

    def test_unknown_charset_is_explicit(self):
        raw = (b"From example envelope\nDate: Tue, 01 Apr 2025 10:00:00 -0400\n"
               b"Content-Type: text/plain; charset=not-a-real-charset\n\nHello")
        record, reason = normalize(raw, Path("synthetic.mbox"), 0)
        self.assertIsNone(reason)
        self.assertIn("charset_decode_fallback_utf8_replacement", record["extraction"]["warnings"])

    def test_html_body_recovers_from_omitted_head_end_without_exposing_metadata(self):
        for closing in ("</head>", ""):
            with self.subTest(head_end=closing):
                message = mail('<html><head><title>Private metadata</title>'
                               '<style>hidden stylesheet</style>' + closing +
                               '<body><p>Order confirmation: four tickets.</p>'
                               '<script>hidden script</script><style>hidden body style</style>'
                               '<p>Total: $84.</p></body></html>')
                message.set_type("text/html")
                raw = mbox(message)
                record, reason = normalize(raw, Path("synthetic.mbox"), 0)
                self.assertIsNone(reason)
                self.assertEqual(record["text"], "Order confirmation: four tickets.\n\nTotal: $84.")
                self.assertEqual(record["source"]["sha256"], hashlib.sha256(raw).hexdigest())

    def test_rejections_and_no_topic_filter(self):
        message = mail("Unrelated bicycle maintenance.")
        message["X-Gmail-Labels"] = "Inbox, Category Promotions"
        self.assertEqual(normalize(mbox(message), Path("s.mbox"), 0)[1], "promotions_label")
        for date, reason in ((None, "missing_or_multiple_dates"), ("bad date", "invalid_date"), ("Tue, 01 Apr 2025 10:00:00 -0000", "date_without_timezone")):
            message = mail()
            del message["Date"]
            if date:
                message["Date"] = date
            self.assertEqual(normalize(mbox(message), Path("s.mbox"), 0)[1], reason)
        message = mail("")
        self.assertEqual(normalize(mbox(message), Path("s.mbox"), 0)[1], "no_readable_body")

    def test_size_limit_and_exact_duplicates_are_audited(self):
        raw = mbox(mail())
        records, decisions = io.StringIO(), io.StringIO()
        worker = Normalizer(io.BytesIO(raw), Path("s.mbox"), records, decisions, set(), len(raw))
        entry = {"decision": "retained", "oversized_headers": False, "offset": 0, "length": len(raw)}
        worker.write(json.dumps(entry))
        worker.write(json.dumps(entry))
        worker.max_message_bytes = len(raw) - 1
        worker.write(json.dumps(entry))
        self.assertEqual(worker.counts["normalized_messages"], 1)
        self.assertEqual(worker.counts["duplicate_exact_raw_messages"], 1)
        self.assertEqual(worker.counts["message_size_limit_messages"], 1)

    def test_end_to_end_output_is_valid_and_cannot_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "input.mbox"
            raw = mbox(mail())
            source.write_bytes(raw)
            output = root / "normalized"
            report = run([source], output, len(raw), len(raw))
            self.assertEqual(report["status"], "complete")
            self.assertEqual(source.read_bytes(), raw)
            records = [json.loads(line) for line in (output / "records.jsonl").read_text().splitlines()]
            render(records, {"version": 1, "articles": []})
            with self.assertRaises(FileExistsError):
                run([source], output, len(raw), len(raw))


if __name__ == "__main__":
    unittest.main()
