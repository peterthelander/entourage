# Initial model-generated article plans

Status: Pilot complete; no model plan accepted for automatic publication.
Date: October 22, 2026.
Review: Coding-agent semantic review complete; independent human review pending.

## Outcome

The configured local model can propose topic groupings and draft claims, but these
trials do not support autonomous memory publication. Of four trials with the revised
prompt, one passed structural and exact-quote validation. That result still made an
overconfident historical-event claim. Neither real-mail trial passed quote checks,
and both also contained unsupported state/completion claims. No unedited model
output was accepted as a publishable memory article.

A separately reviewed, corrected three-article candidate was rendered from the real
sample. This demonstrates the review boundary, not autonomous generation quality.
Nothing was written into the service's live memory or tested through live retrieval.

## Runner and boundaries

`ingestion/src/propose_articles.py` accepts 1–12 complete normalized records with
at most 24,000 UTF-8 bytes of model-input JSON. It sends ID, kind, title, observed
timestamp, optional event date and text. It omits file locators and additional email
headers, but text bodies can contain personal data. No input text is silently cut.

This initial runner uses the llama.cpp provider selected in ignored
`server/data/inference.json`; it does not modify production configuration, restart
the service, use agent tools, alter the database or fall back to hosted inference.
The run uses the existing server virtual environment's httpx dependency. The model
was local gpt-oss-20b MXFP4 on the configured Mac inference server.

The runner requests nonstreamed completion, low reasoning effort and 4,096 maximum
output tokens, with a 2 MiB response cap and network-operation timeout. Temperature
and seed are server defaults, so this is not a controlled deterministic comparison.
Every request, response, input snapshot, input/runner hashes, completion reason,
reported usage and duration are saved privately. Plans passing validation get a
separate plan file; validation never silently fixes JSON, fields or quotations.
Semantic review remains pending in generated reports until a separate review is
recorded. Network requests run directly against the configured inference origin.

Reproduce with a fresh destination, from repository root:

```powershell
server/.venv/Scripts/python.exe ingestion/src/propose_articles.py --records ingestion/fixtures/memory-records.jsonl --config server/data/inference.json --output ingestion/data/reports/article-synthetic-new --repeats 2
```

The source prompt is generic: it specifies article structure, evidence quotations,
uncertainty and distinctions between statements, interpretations and suggestions.
It contains no subject-specific rules. It treats source text as untrusted data;
resistance to adversarial source instructions was not evaluated by this pilot.

## Trials and review

The four-record synthetic sample covers a garden workday and date correction,
a bicycle-service receipt and a reading-circle invitation. The three-record real
sample was hand-selected for short, unrelated source bodies: a service notification,
an account-terms announcement and an order notice. These are convenience samples,
not an unbiased test or evidence of corpus-wide quality.

| Prompt/sample | Repeats | Mechanical passes | Unedited plans accepted after semantic review |
| --- | ---: | ---: | ---: |
| Initial / synthetic | 2 | 0 | 0 |
| Revised / synthetic | 2 | 1 | 0 |
| Revised / real | 2 | 0 | 0 |

Initial failures: a string version instead of a number, and omitted `links` fields.
Review also found the phrase "current confirmed" applied to a historical proposed
date. The revised prompt added an explicit JSON example, mandatory empty lists and
a clearer historical-evidence rule. Original failures remain preserved.

The revised synthetic pass grouped related records and preserved the date correction,
but inferred that the workday "will occur" on the revised date. A changed plan is
not proof of occurrence or an event still being upcoming. It also left unknowns
empty. The other repeat produced malformed closing brackets. No repair was applied.

Both real repeats reformatted a multiline quote so it no longer exactly matched
the source. More seriously, both inferred shipment or delivery from a plain-text
order-status display containing several possible progress stages. One cited an
order identifier, and another cited an order-history navigation link, neither of
which supported the claimed state. Both turned announced future account changes
into completed historical changes. These illustrate why exact quotations alone
cannot prove that a claim follows from its evidence.

Private original artifacts are under ignored `ingestion/data/reports/`:

- `article-synthetic-local-20261022/`: initial prompt, two model trials.
- `article-synthetic-v2-20261022/`: revised prompt, two synthetic trials.
- `article-real-v2-20261022/`: revised prompt, two real trials plus reviewed plan
  and explicit review notes.
- `article-synthetic-20261022/`: initial sandbox connection failures, not model trials.

## Reviewed candidate

The corrected plan in the real-trial directory was authored/reviewed by the coding
agent after examining the sources and both drafts. Its changes are explicit:
describe what the notifications say, preserve planned versus completed status,
replace the invalid quote with literal source text, avoid item-content details not
established by body evidence, and add unknowns for collection/delivery, conditional
account features and uninspected external terms. It is not counted as a model pass.

Rendering produced one dated source journal, three dated instance articles, an
index and retained input/plan sidecars under ignored
`ingestion/data/candidates/article-real-reviewed-20261022/`. Independent review and
live agent retrieval evaluation are still pending.

## Next experiment

Keep publication gated. Improve structured output compliance separately from claim
quality; do not weaken literal-quote checks to turn these failures into passes.
Add reusable evaluation cases for ambiguous progress displays, proposed versus
completed events and evidence that is authentic but does not support the claim.
Inspect whether MIME-to-text normalization discards status cues before choosing a
fix. Compare reviewed drafts on held-out mixed-topic records and repeat successful
cases. Consider article usefulness and selection of durable personal context too:
one article per transactional notice is not established as the right long-term
organization. No additional automatic filtering or topology is selected here.
