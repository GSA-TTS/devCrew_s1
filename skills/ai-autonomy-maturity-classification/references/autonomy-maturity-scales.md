---
created: "2026-11-04T19:17:25Z"
updated: "2026-11-04T19:25:13Z"
---

# Autonomy and maturity scales

Two independent scales. Autonomy is what the system is allowed to do without a human; maturity is how far that behaviour has been proven and scaled in real use. Score both, separately, every time; neither predicts the other.

Pairings that one blended score would hide:

- L5 / M0: a fully autonomous multi-agent system shown only in a paper or code demo, never connected to a live system or paying customer.
- L4 / M4: a system that acts only after a human approves each consequential step, running enterprise-wide, disclosed in official filings, with mature monitoring and rollback. Typical of large regulated-industry deployments that reach scale.
- L2 / M3: a collaborative agent working interactively with a human, live in production for one business unit with a named owner and tracked KPIs.

## Autonomy level (L0 to L5)

Defining question: when the system takes an action, whose decision was it, and how many actions does it take before a human is involved again? This measures the human's role, as the source describes who does what; it is not the model's raw capability.

| Level | Name | User's role | Definition | How to recognize it in a source |
|---|---|---|---|---|
| L0 | No autonomy (baseline) | Full control | No AI agent; a human or deterministic software performs every step; not agentic | Dashboards, rule-based scripts, static RPA |
| L1 | Operator | Directs every action; agent supports or suggests on demand | Agent assists but never acts independently; it executes the actions the human directs, a copilot, not an actor | AI-assisted, co-pilot, carries out each step the user directs |
| L2 | Collaborator | User and agent both plan, delegate and execute, with frequent back-and-forth | Agent executes sub-tasks in tight parallel with a human who stays engaged throughout | Works alongside, human and AI jointly, multi-turn tool use with a human present throughout |
| L3 | Consultant | Agent takes initiative over extended periods; user gives indirect guidance | Agent runs multi-step workflows, consulting the human periodically, not per action | Runs autonomously with periodic check-ins, human reviews outputs not every step |
| L4 | Approver | Passive: approves consequential or irreversible actions, or supplies credentials | Agent works inside guardrails and escalates only blockers or high-stakes decisions | Human in the loop for approval only, escalates exceptions, approval-gate architecture |
| L5 | Observer | Can only monitor or emergency-stop | No routine human decision input; trajectory changeable only by kill-switch | Fully autonomous, lights-out operation, no human in the loop |

L1 applies only when the system itself executes actions the human directs. Recommends and drafts for review are decision-support phrases: a system whose only output is a recommendation or a draft that a person then acts on or signs is AI-assisted decision support, with no L-tag.

Optional sub-scores, only when the source gives enough detail: a relative 1 to 10 autonomy sub-score and a 1 to 10 risk or stakes sub-score. They separate two L4 systems such as an approval-gated marketing-copy generator and an approval-gated grid-dispatch system. They add texture and never replace the L-tag.

## Deployment maturity (M0 to M4)

Defining question: is this running against real data, users or systems right now, and how much of the relevant business does it touch?

| Stage | Name | Definition | Evidence markers |
|---|---|---|---|
| M0 | Research or academic prototype | Paper, technical report or open-source demo; not a product, not run on production data or systems | Preprint, workshop demo, code repository with no named enterprise user |
| M1 | Proof of concept | Validated on a controlled or representative dataset or sandbox; not connected to live systems or real customers | We built a PoC, internal demo, validated in a test environment |
| M2 | Pilot | Real but limited-scope data, users or systems; time-boxed, small group or single site, framed as experimental | Piloting with a named party, one facility, branch or team, a named timeframe, evaluating before wider rollout |
| M3 | Limited production | Live for a defined part of the business, with an accountable owner, monitoring and a real budget line; not company-wide | In production for a named unit, named KPIs tracked, named owner or team |
| M4 | Full production at scale | Enterprise-wide or across most of the function, integrated into core processes and governance, mature monitoring and rollback | Company-wide rollout, disclosed in filings or earnings as operating practice, sustained use confirmed by a later follow-up |

Verification for M3 and M4:

- Do not code a headline finding M3 or M4 on one vendor's or one customer's word alone.
- Required: a second, independent source corroborates the production claim. Without one, keep the claimed tag and flag it unverified, single-sourced.
- Also diagnostic, not required: the deployment is still referenced a year or more later. Sustained mention raises confidence; silence after a one-time press release suggests it may have lapsed. Note it when found.

## Policy or regulatory framework only

Use the tag Policy-Only instead of an M-stage when the finding is a governance, regulatory or standards artifact (proposed rule, statute, agency policy memo, standards framework, procurement guideline) and the source describes no specific system running under it.

- Give an L-tag only when the framework specifies a required or expected autonomy posture (a rule mandating human approval gates for a decision type takes the L-level it mandates); otherwise autonomy is N/A.
- Never infer a maturity stage from how mature compliant deployments probably are; record the rule, not the practice.
- When one source describes both a framework and a specific system operating under it (for example a use-case inventory entry naming a deployed tool), split it into two linked findings: one scored normally, one tagged Policy-Only.

## Ambiguous or inflated claims (agentic-washing)

The tags describe what the finding claims. How far to trust the claim is a separate field; never fold distrust into the L or M tag. A low-credibility post claiming L5/M4 is recorded as a claimed L5/M4 with its doubt carried beside it.

When more than one tag is plausible:

1. Vague source: default to the lower level on both scales. Phrases such as significantly improved, game-changing or fully autonomous without operational detail are marketing quantifiers, not evidence; note the ambiguity.
2. Apply the defining questions before accepting the source's own agentic framing. A relabeled chatbot, single-turn copilot or brittle scripted automation does not clear the L1 bar, whatever it is called.
3. A confident maturity claim from a single self-interested source, with no independent corroboration: record the claimed tag and flag it unverified, single-sourced; do not present it as confirmed.
4. Complexity raises skepticism. An elaborate multi-agent architecture is not more credible about production status; more moving parts historically means a higher chance of stalling before production, since multi-agent pilots often fail on coordination or verification gaps.
5. When trust and the claimed tag pull apart, keep both; do not average. A regulator filing describing a modest L2/M2 pilot is more trustworthy than an unverified post claiming L5/M4, but that belongs in the trust note; each tag reflects only what its source claims.

## Notation

```text
[L<autonomy>/M<maturity>, <year found or dated>]
[L<autonomy or N/A>/Policy-Only, <year>]
```

Worked examples (own wording):

- A utility describes an agent that reconciles meter-read exceptions by querying two billing systems and proposing corrections that a billing clerk works through with it line by line; it has run in one regional billing office for a year with a named owner and KPIs. Tag: [L2/M3, 2025]. The clerk stays engaged (Collaborator); production in one unit.
- A national standard requires that any AI used in licence revocation keep a human approver for every revocation, and names no deployed system. Tag: [L4/Policy-Only, 2026]. The rule mandates an Approver posture; there is no deployment to stage.

## Architecture patterns

Use the pattern to judge whether an agentic claim clears the bar and to describe the system precisely. Production systems often combine patterns: record the dominant one and note hybrids.

| Pattern | Description |
|---|---|
| Single agent with tools | One LLM-driven agent with a defined tool or function-calling surface |
| Orchestrator-worker (supervisor) | A coordinator plans and routes sub-tasks to workers, then merges outputs |
| Hierarchical (manager-subagent) | Several supervision layers partitioning context |
| Peer-to-peer (mesh) | Agents talk directly, no central coordinator |
| Blackboard (shared memory) | Agents read and write a shared state store |
| Swarm (decentralized) | Emergent coordination, no orchestrator |
| Human-in-the-loop approval gate | Mandatory checkpoint before irreversible or high-value actions, on any topology |
| RAG-augmented agent | Agent retrieves from a document store before acting |

When a finding names a specific agent framework or interoperability protocol (for example the Model Context Protocol or Agent2Agent), record it: it is a verifiable detail that can be checked against the vendor's case-study material and shows which ecosystem the customer committed to. Adoption claims about frameworks and protocols change quickly; check current documentation before treating them as stable.
