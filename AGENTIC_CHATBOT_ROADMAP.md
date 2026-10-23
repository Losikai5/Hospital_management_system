# Hospital chatbot: daily implementation guide

Status: planned, implementation not started through this roadmap.
Prepared: 23 October 2026, from a source review of the hospital AI and the BAISOFT architecture discussion.

## Purpose and working agreement

Build an assistant that understands a user's goal, selects approved tools, asks for missing information, performs authorized actions, and explains verified outcomes. Make it dependable enough for a deliberately limited production release before expanding its responsibilities.

A “day” below is a work session, not a deadline. A day may take several calendar days. Finish its acceptance checks, record the result, then stop and rest. Start the next day only when the user asks to continue. Never skip an unfinished dependency just to match the calendar.

This document is a guide, not evidence that a feature exists or a security/compliance certification. Check the current repository before each change. Reuse its business services and permission model rather than duplicating them. Do not change production records during development; use synthetic hospital data.

At the end of every day, update this file with status, changed files, checks performed, unresolved issues, and the exact next step. Keep migrations, rollback considerations, and configuration changes in the daily record. If requirements change, update the remaining plan before implementing the new scope.

## What “agentic” means here

The assistant can choose among approved tools, inspect their results, and decide whether another tool call or a clarification is needed. It can carry a task across conversation turns and resume a pending confirmation. Its autonomy is bounded by server-enforced permissions, action policies, time/cost limits, and explicit workflow states.

Example target flow:

```text
User: Find my upcoming appointment and move it to Friday morning.
  → Identify authenticated user and authorized appointments.
  → Ask which appointment if more than one matches.
  → Retrieve actual available Friday slots.
  → Ask the user to choose a slot when necessary.
  → Prepare a specific rescheduling proposal.
  → Obtain confirmation tied to that proposal.
  → Recheck authorization and availability.
  → Call the hospital's rescheduling service.
  → Return the saved booking result and record the action.
```

The assistant must be able to refuse a tool call, report that an action did not happen, or hand control to a human. More tool calls do not imply better autonomy.

Initial scope: administrative assistance, authorized appointment information/actions, and approved operational information. Diagnosis, prescribing, autonomous clinical decisions, broad patient exports, and financial/pharmacy writes remain outside the initial release. Expanding those areas requires a separate reviewed scope and domain-specific acceptance criteria.

## Starting point: what exists and what needs improvement

| Area | Observed implementation | Planned improvement |
| --- | --- | --- |
| Graph | `ai/orchestrator.py` classifies into user/general/database read/database write | Typed decisions, clarification, tools, confirmations, bounded recovery |
| Database path | Both read and write intents generate SQL and execute it | Authorized domain tools; separate reporting from mutations |
| SQL validation | `ai/sql_validator.py` checks one statement and allowed top-level operation | Runtime restrictions and authorization; eliminate generic write SQL from assistant actions |
| Execution | `ai/service.py` uses Django connection and `fetchall()` | Scoped queries, limits, timeouts, controlled result schemas |
| Identity | JWT middleware attaches a user; invalid tokens become anonymous | Reject unauthorized chat access and verify ownership throughout the lifecycle |
| Permissions | Existing core permission classes and appointment ownership checks | Reusable policy functions enforced by AI tools as well as normal application paths |
| Memory | `AgentState` has no messages; graph has no checkpointer | Conversation/message models plus persistent graph state |
| Follow-ups | SQL prompt accepts `query_context`, but node does not supply it | Real context passed to decision and tool workflows |
| User state | A Django user object is passed into graph state | Serializable IDs; current permissions loaded at execution time |
| Transport | Synchronous WebSocket handler returns a final answer | Explicit request IDs, status, errors, reconnect support, streaming |
| Services | Appointment, billing, pharmacy, user services already exist | Reuse appropriate existing services and inspect their invariants |
| Audit | `apps/audit` exists | Integrate assistant action records with existing audit conventions |

BAISOFT concepts worth borrowing: checkpointed conversation messages, explicit routing and pauses, request correlation, permission gates, retrieval, background ingestion, and simulated integration scenarios. Do not copy its unfinished document-store integration, JSON chat persistence races, or assumption that checkpoints alone recover a disconnected workflow.

## Intended architecture

```text
Authenticated WebSocket/API
  → Validate envelope, conversation ownership, and request uniqueness
  → Load authorized conversation state
  → Decide: answer / clarify / retrieve / invoke approved tool
  → Authorize and validate every tool invocation
  → Read result OR prepare confirmed action
  → Execute through existing hospital domain services
  → Persist outcome and audit record
  → Return/stream a grounded response
```

PostgreSQL stores application messages, action records, and LangGraph checkpoints with distinct responsibilities. Redis may coordinate events and distributed locks; it is not the sole record of completed actions. Celery handles suitable background work, such as indexing and notifications. Core action outcomes must be committed before success is reported.

## Phase A — Establish boundaries and a dependable foundation

### Day 1 — Agree on scope and map current behavior

**Implement/document:** trace `config/consumers.py`, JWT middleware, all `ai/` files, role/permission definitions, appointment services, and existing audit infrastructure. Create a capability matrix: who may ask what, which actions are permitted, which need confirmation, and which are excluded. Establish synthetic users and representative conversation scenarios.

**Why:** permission and product boundaries must be explicit before adding autonomy.

**Done when:** the capability matrix, current flow, initial release scope, and baseline examples are recorded; existing relevant checks have been run and failures documented. No live data is needed.

### Day 2 — Enforce chat authentication and input boundaries

**Implement:** reject missing/invalid authentication at connection or before any model/tool work. Validate message type, required text, size, and malformed JSON. Add consistent error envelopes. Define handling for expired tokens and revoked/deactivated accounts during long connections; validate WebSocket origins for the deployment.

**Done when:** anonymous/inactive users cannot invoke the assistant; malformed messages fail cleanly; valid users can connect. Tokens and credentials do not appear in response/log payloads.

### Day 3 — Define a typed AI contract and safe interim routing

**Implement:** typed intent/decision outputs and predictable error states. Separate read and write routes. Temporarily refuse unsupported writes rather than sending them through raw SQL while the action workflow is being built. Define which requests need clarification and how invalid model output is handled.

**Done when:** unexpected intent values cannot break routing; ambiguous writes request clarification or explain that the action is unavailable; each supported route has a clear result/error contract.

### Day 4 — Extract reusable authorization policies

**Implement:** inspect existing `HasCustomPermission`, appointment ownership, and service rules. Introduce reusable policy/query-scoping functions without weakening existing API behavior. Determine patient, doctor, staff, and hospital scopes from authenticated identity. Apply policies server-side, regardless of model arguments.

**Done when:** synthetic cross-user/cross-scope requests are denied; privileged access works only for explicitly permitted roles. Test both existing endpoints and the new policy interface.

### Day 5 — Build the first authorized read tools

**Implement:** a small registry with typed inputs/outputs, descriptions, and required policies. Start with useful appointment operations supported by existing models: list my appointments and get an authorized appointment's details. Use bounded results and minimal fields. Route these questions through tools instead of arbitrary SQL.

**Done when:** valid requests return only authorized records; guessed IDs and extra model-supplied identity fields cannot expand access. Tool results distinguish empty, denied, and failed outcomes.

### Day 6 — Decide and constrain reporting access

**Implement:** decide whether the initial scope actually needs generated SQL. Prefer approved report functions. If retained, isolate it to restricted read-only database access with allowlisted data, statement limits, timeouts, result caps, and independent scope enforcement. Inspect nested queries/functions, not just the top-level SQL operation. Do not expose generic writes.

**Done when:** the chosen reporting approach has documented access boundaries and meaningful adversarial checks. Broad reads, sensitive fields, prohibited operations, and oversized results fail safely.

## Phase B — Make conversations durable and coherent

### Day 7 — Add conversation and message records

**Implement:** design models in `chat/` for conversations and ordered messages, with ownership, stable message/request identifiers, and timestamps. Enforce ownership on listing, reading, and continuing a conversation. Persist messages needed for the next turn without depending on a slow background queue. Define retention and deletion behavior.

**Done when:** two users cannot read or continue each other's chat; duplicate request delivery does not duplicate a message; message ordering is deterministic. Migrations and rollback notes are recorded.

### Day 8 — Wire recent messages into every relevant AI decision

**Implement:** add serializable message context to `AgentState`; replace stored user objects with IDs. Feed context to classification, clarification, tool selection, and response generation. Start with a configurable recent window and token budget; keep historical records separate. Record all delivered assistant paths, including fallbacks.

**Done when:** “show my appointments” then “only tomorrow” works; a new unrelated question does not inherit inappropriate filters; repeated identical messages are distinguished by IDs rather than text matching.

### Day 9 — Introduce PostgreSQL checkpoints

**Implement:** configure the persistent saver and connection lifecycle. Use a server-derived user/conversation thread identifier. Define which state belongs in checkpoints, reset per-turn fields, and keep transient ORM/connection objects out. Establish checkpoint retention/cleanup independent of message-window trimming.

**Done when:** a saved conversation can continue after process restart and from another worker. Permission information is refreshed rather than trusted indefinitely from a checkpoint. Database failure produces an honest error.

### Day 10 — Handle duplicate and overlapping turns

**Implement:** stable request IDs, durable statuses, idempotency claims, and a per-conversation serialization policy. Decide whether a second request waits or is rejected while another runs. If using distributed locks, specify expiry, ownership, release, and recovery. Define authority between messages, checkpoints, and action records.

**Done when:** duplicate delivery does not repeat work; simultaneous turns do not mix contexts; an abandoned request can be identified and recovered without blindly repeating an action.

## Phase C — Add bounded tool-driven reasoning

### Day 11 — Implement the bounded tool loop

**Implement:** the model chooses approved tool names and typed arguments; the server validates, authorizes, executes, and returns structured results. Limit tool calls, elapsed time, result size, and model usage per request. Restrict parallel calls to independent reads. Handle unavailable tools and invalid arguments explicitly.

**Done when:** a multi-step read task succeeds, an invented tool is rejected, and a looping model stops within configured limits. Record tool events and outcomes, not private model reasoning.

### Day 12 — Add clarification and structured task context

**Implement:** structured pending tasks for incomplete goals. Ask focused questions for missing dates, ambiguous appointment matches, or unavailable choices. Retain selected entity IDs and their authorized provenance rather than guessing from prose. Support correction, cancellation, and switching tasks.

**Done when:** ambiguous requests never silently choose a record; a follow-up supplies the missing field; switching tasks clears inappropriate pending selections.

### Day 13 — Add action previews and durable confirmations

**Implement:** persist proposed action, authorized actor, target, exact arguments, expiry, and status. Bind confirmation to that proposal and its version. Display the proposed change clearly. A model-generated “yes” cannot confirm an action; require an authenticated user event. Recheck permissions and current facts after confirmation.

**Done when:** expired, altered, foreign-user, and replayed confirmations cannot execute. A changed booking/slot forces revalidation or a fresh proposal. No write occurs before the action policy permits it.

### Day 14 — Implement one complete appointment action

**Implement:** choose one action from Day 1's scope, such as rescheduling, and call the existing appointment service. Preserve validation, availability rules, transaction handling, and notification behavior. Add an idempotency key and stable action result. Refactor shared business rules if necessary instead of bypassing them with SQL.

**Done when:** one confirmed request produces one valid change; a repeated confirmation does not repeat it; conflicts return a useful response. Success is based on the committed service result.

### Day 15 — Expand the approved action set carefully

**Implement:** add the next approved appointment actions one at a time. For each, document required fields, permissions, ownership rules, confirmation policy, transaction boundary, and reversal options. Keep unsupported billing, clinical, and pharmacy mutations disabled.

**Done when:** every enabled action has policy checks, useful failures, audited outcomes, and positive/negative scenarios. If this takes multiple sessions, split Day 15 into named action subdays.

### Day 16 — Recover from tool and model failures

**Implement:** distinguish validation failures, authorization denial, service conflicts, provider failure, timeout, and unknown action outcome. Retry only suitable transient failures within a budget. For uncertain writes, inspect the durable action record before considering another execution. Offer a human handoff with useful task context.

**Done when:** a connection failure after a committed write cannot cause duplicate execution; unavailable services do not yield fabricated success; cancelled work does not claim a committed action was undone.

## Phase D — Add authorized knowledge retrieval

### Day 17 — Build document ingestion and job status

**Implement:** if document assistance is in scope, create a versioned catalog for approved administrative documents, ownership/access metadata, and background ingestion jobs. Pick an embedding model, compatible vector dimensions, and consistent collection strategy. Choose chunking based on actual documents; 1,000 characters/200 overlap from BAISOFT is a starting experiment, not a requirement.

**Done when:** documents index successfully with traceable source/version/chunk IDs; retries do not multiply chunks; failed jobs expose useful status; removed or superseded versions stop being retrieved.

### Day 18 — Add retrieval tools with references

**Implement:** retrieve only authorized, current document passages, attach usable citations, and separate retrieved text from instructions. Handle insufficient evidence and contradictory versions. Integrate a document tool into the existing bounded loop instead of building an unrelated assistant.

**Done when:** cited text supports the answer; restricted documents cannot be retrieved by unauthorized users; malicious instructions inside a document cannot authorize tools or change application policies. No matching evidence produces an honest response.

## Phase E — Make the user experience and operations dependable

### Day 19 — Add progress, streaming, and reconnect behavior

**Implement:** request-correlated events for accepted, working, clarification, confirmation, result, and error. Stream answer text where useful using an appropriate async/worker architecture. Never label an uncommitted action successful. Add reconnect lookup/resume behavior based on durable request/action IDs, not the lifetime of one socket.

**Done when:** users can reconnect without duplicate actions, status events belong to the right request, slow tasks do not freeze unrelated connections, and cancellation semantics are documented.

### Day 20 — Integrate audit, privacy, and operational metrics

**Implement:** reuse `apps/audit` conventions for actor, action, target, authorization outcome, request ID, and final status. Redact unnecessary personal data, tokens, raw SQL/results, and prompts from routine logs. Define access and retention for conversations, checkpoints, embeddings, and audit records. Add latency, failures, tool usage, model cost, and queue-depth metrics.

**Done when:** an authorized operator can trace an action without unnecessary patient-data exposure; logs support failure diagnosis; retention/deletion procedures cover all relevant storage layers. Legal/organizational obligations require separate owner review.

### Day 21 — Build repeatable agent evaluations

**Implement:** turn baseline examples into a versioned synthetic evaluation set. Cover happy paths, multi-turn references, ambiguity, invalid tool arguments, cross-user access, confirmation replay, denied actions, prompt injection, duplicate delivery, restart recovery, and provider failure. Use deterministic tool/policy tests plus limited real-provider evaluations.

**Done when:** safety-critical permission and duplicate-action checks pass; task completion, grounding, latency, and cost targets are agreed and measured. Record model/prompt versions with results. Do not mistake a high average answer score for permission correctness.

### Day 22 — Exercise failure, concurrency, and deployment behavior

**Implement:** stage realistic concurrent chats, overlapping requests, worker restarts, Redis outage, database outage, model rate limits, and delayed background jobs. Test backup/restore and migrations against a staging environment. Confirm that the system fails safely when required state cannot be persisted.

**Done when:** no observed cross-user context leakage or duplicate mutation; recovery procedures are demonstrated; latency/capacity limits and remaining failure modes are documented.

### Day 23 — Prepare deployment controls and support procedures

**Implement:** staging/production configuration, secret management, least-privilege database roles, transport security, migrations, model/tool versioning, and feature flags. Provide a kill switch for mutations and fallback to read-only assistance. Write runbooks for provider outage, stuck action, permission incident, restore, and rollback. Define owners and alert thresholds.

**Done when:** a second developer can deploy and roll back using the runbook; disabled actions cannot execute through another route; health checks distinguish transport, model, database, and worker problems.

### Day 24 — Run a controlled pilot

**Implement:** start with approved users and narrow enabled tools. Review failure cases and feedback against the evaluation set. Use explicit approval for any real operational actions. Compare service outcomes with what the assistant reported. Fix blockers and rerun affected evaluations before widening access.

**Done when:** pilot exit criteria set before launch are met, unresolved risks have named owners, and a release decision is recorded. Otherwise add remediation days and repeat the pilot.

### Day 25 and beyond — Expand deliberately

Each new capability gets its own mini-cycle: define scope → policies → typed tool → domain validation → confirmation/recovery rules → tests/evaluations → limited pilot → release. Add summarization or richer retrieval only when observed context limits justify it. Reevaluate after model changes, schema migrations, permission changes, and new integrations.

Production readiness is an ongoing process. Do not declare it complete because the graph can call tools or because the numbered days are finished.

## Release gates

All apply to the initial agreed scope:

- Authenticated identity, conversation ownership, and record-level access are enforced outside the model.
- Every enabled tool has a narrow contract and authorization tests.
- Writes use approved domain services, confirmations where required, durable idempotency, and audit records.
- Follow-ups survive restart without mixing users or restoring stale privileges.
- Retries and reconnects cannot silently repeat mutations.
- Answers are grounded in tool/document outcomes; failures are visible and honest.
- Model/tool budgets, database limits, rate limits, and concurrency behavior are enforced.
- Logs, retention, access controls, backup/restore, monitoring, and rollback have been reviewed and exercised.
- Evaluation targets and pilot exit criteria are met; remaining issues have explicit disposition.

## Daily implementation record

Copy this block for each session:

```text
Day / date:
Status: not started | in progress | blocked | complete
Goal:
What changed and why:
Files / migrations / configuration:
Checks run and actual results:
Observed limitations or failures:
Rollback notes:
Acceptance criteria met / still outstanding:
Next session's exact starting point:
```

Initial status: all days are planned. The source scan has been completed, but Day 1's capability agreement and baseline checks still need to be carried out.

To continue in this chat: “Start Day 1 from AGENTIC_CHATBOT_ROADMAP.md.” In a later session: “Read the roadmap and daily record; continue the first unfinished day.”
