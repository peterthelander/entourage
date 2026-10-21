# Design principles

These principles guide changes to Entourage's code, context assembly, prompts,
and model behavior. Add principles as we learn from concrete problems.

## Development and engineering

How we investigate problems, evolve the implementation, and keep the codebase
simple and coherent.

### Diagnose the cause before patching the symptom

When something looks wrong, first understand how the surrounding system produced
it. An unexpected answer or code failure is evidence to investigate, not a
complete diagnosis or an implementation request.

Before choosing a fix:

- Trace the relevant inputs, state, and execution path. Separate observed facts
  from hypotheses about the cause.
- Consider whether the symptom exposes a broader design weakness, such as how
  context is selected, rather than a defect confined to that one example.
- Use focused tests or controlled experiments when the cause is uncertain.
  For model behavior, compare multiple runs and inspect the actual model input;
  one plausible answer does not establish a cause or prove a fix.
- Choose the simplest change that addresses the demonstrated cause. Prefer a
  coherent rule over accumulating special cases, prompt prohibitions, or
  overlapping recovery paths. Remove superseded workarounds when appropriate.
- Check both the failing case and nearby behavior that should continue working.
  State what the evidence establishes and what remains uncertain.

Keep the investigation proportional to the problem. A small local fix is right
when the evidence shows a small local cause. This principle does not require an
architectural rewrite for every bug; it asks us to understand the problem before
deciding how broad the solution should be.

#### Example: an old request resurfacing in a new conversation

During an apple-picking conversation, Entourage answered an earlier request for
coding improvements. Adding a prompt rule against unsolicited coding requests
would have targeted the visible answer without explaining why it occurred.
Implementing the memory enhancements described in that answer would also have
mistaken the failure output for the user's intended task.

Inspecting the assembled context revealed older coding discussions alongside the
current conversation. Experiments compared full history, timestamps, and
selection based on inactivity gaps. They informed a simpler context-selection
rule: prioritize the current session and keep older conversations available
through memory tools. The results supported that direction without proving that
every similar model failure has the same cause.

### Evolve through experiments and quick feedback

We have clear experience goals, but we do not yet know the best way to achieve
them. Experimentation is an expected part of building Entourage. Memory,
context selection, and other strategies will change as we learn from actual use.

- Keep the goals more stable than the algorithms: a natural, continuous
  conversation, useful recall, and a responsive experience with little friction.
- Treat implementation choices as hypotheses to evaluate, not permanent design
  commitments. Try ideas, observe results, and revise or replace them when the
  evidence warrants it.
- Favor small, reversible experiments with a clear question. Learn from both
  improvements and failures, and record enough context to understand the result.
- Keep the feedback cycle quick. Make it easy to notice a problem, share the
  relevant evidence, investigate it, and try an improvement in everyday use.
- As strategies evolve, remove abandoned experiments and superseded mechanisms
  rather than accumulating complexity. Preserve useful findings so we can build
  on what we learned.

#### Example: copying the latest exchange for investigation

The user can easily copy the latest query and agent response into the coding
agent. This makes real behavior available for investigation without requiring
the user to reconstruct the exchange or explain the implementation. Supporting
details such as the model and recorded tool calls help reproduce the behavior.
The copied response is evidence to interpret in light of the user's intent,
not automatically a request to implement whatever the response suggests.

### Give each responsibility a clear home

Keep ownership of data and behavior clear so the system stays understandable as
it evolves. Prefer a coherent path for each responsibility over competing
implementations that can disagree.

- Make it clear which component owns conversation history, context selection,
  memory retrieval, and action execution. Other components should use that
  owner's interface rather than maintain a competing version of the same state.
- Share rules where consistent behavior is needed. Avoid duplicating orchestration
  or recovery logic across the client, service, and model prompts.
- Place work where its information and capabilities belong. For example, the
  service owns durable conversation execution; the requesting client owns access
  to its device capabilities and permissions.
- Keep boundaries practical. Introduce abstractions when they clarify real
  responsibilities, and remove obsolete paths when their replacements are ready.
  Clear ownership does not require one process, machine, or inference provider.

#### Example: one owner for an agent turn

The Python service assembles context and runs the tool loop. The browser displays
progress and responds to device-tool requests. A browser reconnect should recover
the service's turn state rather than start an independent execution of the same
request.

## Agent experience and behavior

How Entourage should behave for the user, and how we judge whether the
conversation delivers that experience.

### Keep technical boundaries behind a natural, continuous conversation

Entourage should feel like talking with an intelligent person who knows the user
and can pick up earlier conversations. Internal implementation details should
support that experience without becoming concepts the user must manage.

- Keep one continuous conversation. Do not require users to create, select, or
  organize chat threads to preserve context or return to an earlier topic.
- Treat sessions, context windows, storage boundaries, and retrieval as internal
  mechanisms. A pause may change which messages the system supplies to the model;
  it should not create a visible reset or require the user to start over.
- Use memory tools in the background to help the agent recall relevant details.
  Users should be able to speak naturally, without choosing search keywords,
  exporting journals, or knowing which tool provides the information.
- Bring past details into the conversation when they are relevant. Avoid routine
  narration of retrieval steps, tool names, message IDs, or context management.
  Provide supporting details when the user asks or when they help resolve doubt.
- Be honest about uncertainty and missing information. A natural experience does
  not mean pretending to remember; ask a useful question when needed.

#### Example: continuing after a pause

If the user says, "Let's continue planning yesterday's outing," Entourage should
recover the relevant earlier discussion and continue naturally. An internal
session boundary should not force the user to find a thread, enable memory, or
repeat information that the system can retrieve.

### Be clear about knowing, inferring, and doing

Trust depends on the agent's words matching its evidence and actions. Keep these
distinctions accurate without burdening ordinary conversation with disclaimers.

- Distinguish what the user said, what a source establishes, and what the agent
  infers. A remembered statement is not independent verification of its contents.
- Express uncertainty when it matters. Do not fill gaps in memory with plausible
  details or present a guess as a recollection.
- Distinguish offering help, attempting an action, and completing it. Claim
  completion only when the responsible system confirms the outcome.
- Explain failures or incomplete outcomes plainly enough for the user to decide
  what to do next. Do not let fluent language conceal missing evidence or work.

#### Example: remembering friends on an outing

The agent can recall that Tate, Starr, Summer, and Rhett are joining an outing
because the user said so. It should not invent which friend brings snacks or
handles directions. Offering to help with directions also does not mean a route
has been looked up.

### Evaluate whole conversations, not just individual answers

An answer can be sensible in isolation and still be wrong for the conversation.
Judge behavior against the user's current intent and how it changes across
exchanges.

- Test short follow-ups that depend on earlier messages, changes of topic,
  corrections, and references to discussions before a pause.
- Check that completed requests do not silently become active again and that
  relevant past details remain available when the user returns to them.
- Evaluate the experience across context selection, retrieval, tool execution,
  and the final answer. A good intermediate result does not establish that the
  complete interaction works well.
- For variable model behavior, compare multiple runs with representative
  conversations. Keep examples of real failures and check nearby successful
  behavior when evaluating a change.

#### Example: responding to a conversational update

"Going with our friends Tate, Starr, Summer, and Rhett" should be understood in
the preceding apple-picking conversation. A polished coding-improvement request
would still be a failure, even if it answers an older message well. A later
"Who is coming with us?" should recover the names without requiring repetition.
