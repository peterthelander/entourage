# Entourage: Personal Context & Memory Architecture Roadmap

Status: Proposal with implemented milestones noted. Reviewed: October 22, 2026.

This document outlines the conceptual blueprint and technical strategy for implementing persistent, local-first memory in **Entourage**. The goal is to move beyond the artificial boundary of isolated chat threads, providing a unified, self-organizing knowledge base that operates transparently across personal devices.

---

The incomplete former `knowledge-base-ideas.md` has been consolidated here. Its
local workhorse and private Tailscale browser-access ideas are retained below.
SQLite owns durable state; Markdown is the readable memory layer. Local ownership
is a design goal, not a guarantee that optional external tools send no data off-device.

## 1. Core Architectural Pillars

**Current architecture:** Python owns execution and memory operations. SQLite is
authoritative for durable conversations/turns; Markdown is the readable memory
layer. The first implemented milestone is deterministic daily-journal
export with automatic refresh; see [journal behavior](reference/memory-journals.md). Semantic
articles and dreaming below remain future work. Bounded keyword/date retrieval
is now available through the Python `searchMemories` tool; the executing service
refreshes journals automatically and catches up on restart.
Python also exposes inventory and paginated date-based reading so topic summaries
can be grounded without keyword guesses. Stored summaries remain future work.

* **Local Workhorse & Private Access:** A home Mac or Windows machine hosts inference and background processing; a responsive browser reaches the service privately through Tailscale.
* **Locally Owned State, Selectable Inference:** SQLite stores execution/history; local Markdown journals and proposed articles form the readable memory vault. Inference can be local or hosted. For the current owner, local inference is primarily a cost/control choice; see [ongoing work streams](ongoing-work-streams.md).
* **Organic Taxonomy:** Avoid rigid database schemas or pre-defined categorization. Structure should emerge organically from content through LLM-driven refactoring over time.
* **Asymmetric Labor Division:** Real-time capture and lightweight IO happen on mobile/client nodes, while heavy background consolidation ("dreaming") occurs on desktop nodes (e.g., a home Mac or Windows machine).
* **Deterministic Search + Semantic Flexibility:** Pair fast, deterministic text indexing (grep/title matching) with LLM reasoning to retrieve context without hitting context limits or requiring heavy external vector databases.

---

## Guiding use case: planning the Chapin daddy-daughter ski trip

Clarified by the user on October 22, 2026. This is a target experience, not a
claim that the archive has been searched or that the information is available yet.

The user should be able to say: "I'm getting ready to make plans for the Chapin
daddy-daughter ski trip coming up. Can you review what happened in previous years
and help guide me through the steps for this year?"

The agent should find relevant history from ingested email, calendars and other
available sources; reconstruct each year's planning and actual events; and use
that evidence to help prepare this year's plan. Useful details might include
organizers, registration steps, deadlines, bookings, transportation, equipment and
lessons from prior trips, where the sources support them.

Keep years and evidence separate: an invitation establishes a proposal, a booking
establishes a reservation, and neither alone proves attendance. Distinguish
historical arrangements from confirmed requirements for the upcoming trip and
from suggested next steps. Identify gaps or conflicts rather than inventing a
complete history. New dates, prices and requirements need current evidence.

Judge ingestion by whether this conversation works end to end: recover relevant
records across years, preserve links to originals, answer follow-up questions,
and produce a useful planning sequence grounded in history. Smaller files and
well-formed articles are intermediate results. The user should not need to know
export filenames, labels, search syntax or the memory's internal organization.

An initial experiment can assemble a small source-backed ski-trip history from
retained records and check which planning questions it can actually answer.
Record missing evidence and inspect filter decisions if relevant material is
absent. The chosen Promotions exclusion remains in effect; finding relevant
excluded records would be evidence to discuss, not permission to change the rule.

## 2. The Three-Tier Memory Lifecycle

### Layer 1: The Active Stream (Working Memory)
* **What it is:** The daily conversation thread. It handles immediate back-and-forth context and tool execution.
* **Lifespan:** Ephemeral. It operates transparently without requiring the user to manually manage or switch chat threads. Active context is currently selected by inactivity gap, not by midnight; older history remains available through memory tools.

### Layer 2: The Episodic Log (Daily Journals)
* **What it is:** A comprehensive chronological record of what happened, what was discussed, and what actions were taken on a specific date (stored as `YYYY-MM-DD.md`).
* **Design Principle:** Not optimized for byte-size conservation (disk space is cheap), but optimized for searchability, chronological querying, and historical fidelity.

### Layer 3: The Semantic Core (Living Concept Articles)
* **What it is:** A Wikipedia-style collection of evergreen Markdown articles (`article-name.md`) tracking ongoing topics, projects, preferences, and recurring events (e.g., `daddy-daughter-ski-trip.md`).
* **Design Principle:** Articles link to one another using standard wiki-style hyperlinks (`[[article-name]]`). They evolve dynamically as new information is ingested.

---

## 3. The Proposed Asynchronous "Dreaming" Pipeline

The proposed dreaming engine would run in the background (triggered overnight or when processing historical batch dumps like Google Takeout or WhatsApp exports) to distill raw data into structured memory.

### The Multi-Pass Ingestion Loop:
1. **Episodic Pass:** Ingest raw daily logs, message exports, or chat transcripts and synthesize a clean, detailed episodic journal (`YYYY-MM-DD.md`).
2. **Refactoring & Growth Check:** Review existing semantic articles against new information. 
   * *Threshold Rule:* If a topic within a broad article (e.g., `chapin-school.md`) expands past comfortable density thresholds (~2,000 words), split it into a dedicated child article (e.g., `daddy-daughter-ski-trip.md`) and insert clean parent-links.
3. **Horizon & Task Tracking:** For forward-looking projects or recurring events, maintain dynamic instance files (e.g., `ski-trip-2027.md`) featuring active checklists for pending administrative tasks.

---

## 4. Proposed Retrieval Architecture (Fuzzy Matching & Tool Execution)

To resolve user queries without bloating the active prompt context:
* **The Master Index (`index.md`):** A lightweight, compact registry of all core article titles and short keyword summaries that fits instantly into context.
* **Tool-Assisted Lookups:** 
  * *For Specific Historical Events:* The agent extracts temporal and keyword parameters to execute a targeted grep across the daily episodic journals (`searchMemories({ keywords, dateRange })`).
  * *For Ongoing Concepts:* The agent uses semantic reasoning against the `index.md` list to identify, load, and update the relevant living article file.

---

## 5. Immediate Prototyping Milestones

1. **Daily journals (implemented):** Python exports shared-chat records into ignored `server/data/vault/journals/`. Entries preserve source references; execution-enabled services refresh them automatically and catch up on restart. Model summarization remains future work.
2. **Retrieval (implemented baseline):** Python `searchMemories` returns bounded literal keyword/date matches with dated excerpts and source references. Automatic refresh retries failures and catches up after restart. Literal matching and small-model tool selection remain limitations.
3. **Reviewed imported articles (small pilot implemented October 23, 2026):** Python owns explicit reviewed-bundle publication and bounded article/source tools. Unified memory search covers conversation journals and imports separately. Five reviewed sources/articles are live; this is not full-archive ingestion. Incremental updates and autonomous refactoring remain future work.

An isolated [generic candidate prototype](experiments/memory-candidate-contracts.md)
now defines versioned source records and reviewed article plans, rendering imported
source journals, concept/instance articles and an index. Synthetic multi-topic
checks are implemented. Experimental model synthesis and service retrieval are now
available; reliable automatic synthesis, incremental updates and background
consolidation remain future work. See the [current integration status](memory-ingestion.md#reviewed-live-pilot).

Initial [local-model article trials](experiments/2026-10-22-article-generation.md)
now exercise this contract on synthetic and real mixed-topic samples. They exposed
format failures and unsupported completion claims. A separately reviewed candidate
was rendered; no unedited model plan was accepted for live publication.
