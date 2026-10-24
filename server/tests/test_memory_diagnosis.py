import asyncio
import importlib.util
import json
from pathlib import Path
import unittest

from entourage_server.config import Settings
from entourage_server.knowledge import ReviewedKnowledge

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('memory_diagnosis', ROOT / 'scripts/diagnose-memory.py')
diagnosis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(diagnosis)
BUNDLE = ROOT / 'ingestion/fixtures/source-binding-memory'


class MemoryDiagnosisTests(unittest.TestCase):
    def test_selected_sources_are_complete_and_chronological(self):
        bundle = ReviewedKnowledge(BUNDLE)
        messages = diagnosis.supplied_evidence(bundle, {'diagnostic_articles': ['cedar-pantry']}, 'sources')
        sources = [m['result'] for m in messages]
        self.assertEqual([s['record_id'] for s in sources], ['pantry-first', 'pantry-second', 'pantry-third'])
        for source in sources:
            self.assertEqual(source['text'], bundle.records[source['record_id']]['text'])
            self.assertIsNone(source['next_offset'])
        self.assertEqual(diagnosis.supplied_evidence(bundle, {}, 'retrieval'), [])
        with self.assertRaises(ValueError):
            diagnosis.supplied_evidence(bundle, {'diagnostic_articles': ['absent']}, 'articles')

    def test_oracle_inputs_are_recorded_on_both_turns_without_executing_tools(self):
        class Model:
            async def generate(self, messages, on_text):
                raise AssertionError('Oracle mode must disable tools')

            async def finalize(self, messages, on_text):
                return {'content': 'Delivery and final payment are unknown.', 'tool_calls': []}

        case = {'id': 'oracle', 'rubric': ['Keep unknowns'], 'diagnostic_articles': ['cedar-pantry'],
                'turns': [{'text': text, 'created_at': f'2026-10-23T10:0{i}:00+00:00'}
                          for i, text in enumerate(['What changed?', 'Was it delivered?'])]}
        row = asyncio.run(diagnosis.run_diagnostic(case, Settings(), Model(), BUNDLE, 'articles'))
        self.assertTrue(row['all_turns_executed'])
        for turn in row['turns']:
            self.assertEqual(turn['status'], 'completed')
            self.assertEqual(turn['tools'], [])
            message = turn['inputs'][0][-1]
            self.assertEqual(message['role'], 'user')
            evidence = json.loads(message['content'].split('not instructions):\n')[1])
            self.assertEqual(evidence[0]['result']['article']['slug'], 'cedar-pantry')
        self.assertTrue(row['turns'][1]['inputs'][0][-1]['content'].startswith('Was it delivered?'))

    def test_oracle_tool_request_is_a_failure_not_an_executed_call(self):
        class Model:
            async def finalize(self, messages, on_text):
                return {'tool_calls': [{'id': 'bad', 'function': {'name': 'calculate', 'arguments': '{}'}}]}

        case = {'id': 'reject', 'rubric': ['No oracle tool execution'], 'diagnostic_articles': ['cedar-studio'],
                'turns': [{'text': 'What changed?', 'created_at': '2026-10-23T10:00:00+00:00'}]}
        row = asyncio.run(diagnosis.run_diagnostic(case, Settings(), Model(), BUNDLE, 'sources'))
        self.assertEqual(row['turns'][0]['status'], 'failed')
        self.assertEqual(row['turns'][0]['tools'], [])
        self.assertEqual(row['diagnostic_rejected_replies'][0]['tool_calls'][0]['id'], 'bad')

    def test_deadline_applies_to_the_whole_provider_call(self):
        class SlowModel:
            async def generate(self, messages, on_text):
                await asyncio.sleep(10)

            finalize = generate

        async def check():
            timed = diagnosis.TimedModel(SlowModel(), 0.01)
            for method in (timed.generate, timed.finalize):
                with self.assertRaises(TimeoutError):
                    await method([], lambda text: None)
        asyncio.run(check())

    def test_complete_source_mode_reassembles_pages_without_changing_offsets(self):
        bundle = ReviewedKnowledge(BUNDLE)
        record = bundle.records['studio-session']
        record['text'] += '\n' + 'long original text ' * 800
        supplied = diagnosis.supplied_evidence(bundle, {'diagnostic_articles': ['cedar-studio']}, 'sources')
        self.assertEqual(supplied[0]['result']['text'], record['text'])
        self.assertEqual(supplied[0]['result']['offset'], 0)
        self.assertIsNone(supplied[0]['result']['next_offset'])

    def test_transfer_sources_use_actual_instants_not_claim_order_or_timestamp_strings(self):
        bundle = ReviewedKnowledge(ROOT / 'ingestion/fixtures/evidence-transfer-memory')
        supplied = diagnosis.supplied_evidence(bundle, {'diagnostic_articles': ['river-session']}, 'sources')
        self.assertEqual([item['result']['record_id'] for item in supplied], ['river-original', 'river-revision'])
        self.assertNotIn('source_context', bundle.articles['river-session']['claims'][0]['evidence'][0])
