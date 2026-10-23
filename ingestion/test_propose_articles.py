import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parent / "src"))
from propose_articles import check_plan, plan_schema, prepare, resolve_spans, source_spans, structured_format  # noqa: E402


class ArticleProposalTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).parent / "fixtures"
        self.records = [json.loads(line) for line in (root / "memory-records.jsonl").read_text().splitlines()]
        self.plan = json.loads((root / "memory-plan.json").read_text())

    def test_prompt_omits_local_source_metadata_and_preserves_text(self):
        by_id, messages = prepare(self.records)
        inputs = json.loads(messages[1]["content"])
        self.assertEqual(inputs[0]["text"], self.records[0]["text"])
        self.assertNotIn("source", inputs[0])
        self.assertEqual(check_plan(json.dumps(self.plan), by_id), self.plan)

    def test_rejects_missing_fields_wrong_version_and_fabricated_quotes(self):
        for mutation in ("version", "links", "quote"):
            plan = copy.deepcopy(self.plan)
            if mutation == "version":
                plan["version"] = "1"
            elif mutation == "links":
                del plan["articles"][0]["links"]
            else:
                plan["articles"][0]["claims"][0]["evidence"][0]["quote"] = "Never in the source"
            with self.assertRaises(ValueError):
                check_plan(json.dumps(plan), {r["id"]: r for r in self.records})

    def test_rejects_oversized_samples_without_truncating(self):
        records = copy.deepcopy(self.records)
        records[0]["text"] = "x" * 24001
        with self.assertRaises(ValueError):
            prepare(records)
        with self.assertRaises(ValueError):
            prepare([])

    def test_span_compilation_preserves_source_bytes_as_text(self):
        by_id, messages = prepare(self.records, citations="spans")
        inputs = json.loads(messages[1]["content"])
        self.assertNotIn("text", inputs[0])
        span = source_spans(self.records[0])[0]
        self.assertEqual(span["text"], self.records[0]["text"][span["start"]:span["end"]])
        plan = copy.deepcopy(self.plan)
        for article in plan["articles"]:
            for claim in article["claims"]:
                claim["evidence"] = [{"span_id": source_spans(by_id[e["record_id"]])[0]["id"]} for e in claim["evidence"]]
        compiled = resolve_spans(json.dumps(plan), by_id)
        self.assertEqual(compiled["articles"][0]["claims"][0]["evidence"][0]["quote"], span["text"])
        schema = plan_schema(by_id, span_ids=[span["id"]])
        evidence_schema = schema["properties"]["articles"]["items"]["properties"]["claims"]["items"]["properties"]["evidence"]
        self.assertEqual(evidence_schema["items"]["required"], ["span_id"])
        plan["articles"][0]["claims"][0]["evidence"] = [{"span_id": "fabricated"}]
        with self.assertRaises(ValueError):
            resolve_spans(json.dumps(plan), by_id)

    def test_source_span_slices_remain_bounded_without_normalizing_whitespace(self):
        record = copy.deepcopy(self.records[0])
        record["text"] = "A  double space\nwrapped line\n\n" + "z" * 1001
        spans = source_spans(record)
        self.assertEqual(spans[0]["text"], "A  double space\nwrapped line")
        self.assertTrue(all(len(span["text"]) <= 500 for span in spans))
        self.assertEqual("".join(span["text"] for span in spans[1:]), "z" * 1001)

    def test_schema_wrapper_and_required_fields(self):
        records = {r["id"]: r for r in self.records}
        response_format = structured_format(records, "spans")
        self.assertEqual(response_format["type"], "json_object")
        article = response_format["schema"]["properties"]["articles"]["items"]
        self.assertIn("links", article["required"])
        evidence = article["properties"]["claims"]["items"]["properties"]["evidence"]
        self.assertEqual(evidence["minItems"], 1)
        allowed = evidence["items"]["properties"]["span_id"]["enum"]
        self.assertEqual(set(allowed), {s["id"] for r in self.records for s in source_spans(r)})

    def test_accuracy_fixture_rubrics_are_not_model_input(self):
        root = Path(__file__).parent / "fixtures"
        fixture = json.loads((root / "article-accuracy-rubric.json").read_text())
        for partition in fixture["partitions"].values():
            records = [json.loads(line) for line in (root / partition["records"]).read_text().splitlines()]
            by_id, messages = prepare(records, citations="spans")
            self.assertEqual(set(by_id), {row["record_id"] for row in partition["rubric"]})
            for row in partition["rubric"]:
                self.assertNotIn(row["criterion"], messages[1]["content"])


if __name__ == "__main__":
    unittest.main()
