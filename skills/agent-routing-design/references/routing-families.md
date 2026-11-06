---
created: "2026-11-05T00:09:47Z"
updated: "2026-11-05T00:20:22Z"
---

# Routing families: fit conditions and design notes

Use this file to fill the Family fit table and the Architecture line. For each family, the Use when list gives the facts that support a Used verdict, and the Do not use when list gives the facts that force Not used for the decision in question.

## Conditions shared by every family

Do not build a router at all when any of these holds:
- Only one meaningful downstream handler exists, or the handlers differ only cosmetically (prefer one handler with parameters).
- Annotators cannot apply the route definitions consistently.
- A wrong route cannot be detected, corrected, contained or escalated (the missing piece is the feedback path, not the router).
- Traffic is too small to measure improvement over a simple baseline.
- A routing error is catastrophic and no independent guard, confirmation or recovery path exists.

## Rule-based routing

Use when:
- The decision is determined by trusted state: identity, tenant, entitlement tier, contract terms, region, data class, channel, requested path, explicit user choice, modality, token or context length, maintenance state, quota, feature-flag treatment.
- The decision must be reproducible on replay, is a policy decision, must be readable by the people accountable for it, or sits under a tight latency and cost budget.
- A learned router is the goal: ship rules first; the rule router is also the baseline every later router must beat.

Do not use when:
- The discriminating signal is semantic and surface forms are open-ended (keyword matching over free text gives boundary false positives and is easily evaded).
- Nobody can state inclusion and exclusion criteria that two qualified reviewers apply the same way.
- Rules are being added one by one to patch an upstream classifier's mistakes (a correction cascade); improve the model instead.
- Thresholds would be hand-set inside rules over a changing model; learn them on held-out validation data instead.

Design notes:
- Choose the smallest representation that expresses the policy: conditional code for small stable sets; a dispatch table keyed on a discriminator (intent, tenant, tool, model tier); a decision table with an explicit hit policy; a policy engine for authorization-shaped routing; a state machine when routing depends on session state. Move rules from code to data once non-engineers change them or they must be versioned and audited apart from the binary.
- Hit policy: unique for mutually exclusive routes (the default for one handler per request); first for ordered fallback chains (cheap, but it hides overlap); collect or rule order for fan-out or a ranked list handed to a selector; any to catch drift among redundant conditions. Where an engine lacks the policy you need, use an explicit integer priority column and a sort step the router owns.
- Verify the rule set in continuous integration, not on the request path: reject duplicate identifiers and priorities, require an explicit hit policy and a reachable catch-all row, run gap and overlap detection (fail on inconsistent overlaps under unique), run shadowing analysis, and check that every referenced route exists in the registry.
- A general shape: an exact-match dispatch table for bucket selection, then a short ordered rule list per bucket in a compiled, sandboxed expression language or decision table. Normalize input text before matching; rule files from untrusted authors are never accepted as executable code.

## Content-based routing

Use when:
- The item arrives without a trustworthy declaration of what it is or what should happen to it, and materially different handlers exist (parsers, capabilities, capacity pools, risk classes, service objectives).
- Heterogeneous artifacts must be parsed and the parser choice cannot be delegated to the sender's declaration; format detection is a security decision.
- Urgency or sensitivity in the content should change the capacity pool (priority routing).

Do not use when:
- Trusted state already determines the decision.
- The layer cannot see content: gateways that match on host, path, method, headers, port or SNI cannot classify bodies; put payload classification in an application-layer router or a classifier service behind the gateway.
- A nuanced content decision would be expressed in a broker filter language; keep those for cheap, exact, metadata-shaped selection.

Design notes:
- Keep five decisions separate in design, logs and evaluation: format, topic or intent, capability, priority, and policy (deny, quarantine, redact, clarify, escalate).
- Detection runs as a cascade from cheap and deterministic to expensive and probabilistic, with a budget at every tier and a defined outcome when a tier exhausts it: trusted metadata and rules; byte-level format and encoding detection; cheap text checks (patterns, keywords, language identification); embedding similarity to exemplars; a trained classifier; a generative model or an extraction service such as OCR; a human. Escalate only when the cheaper tier abstains or its margin is too small, and record which tier produced the accepted decision.
- Store the payload and pass a reference; screen and contain before parsing; validate and repair a classifier output at most once.

## Embedding-based routing

Use when:
- Route membership is mainly semantic, route examples form stable, separable neighbourhoods, the decision must be cheaper or faster than generative reasoning, and wrong decisions can be contained.
- Typical fits: recurring intent classes, agent or tool selection from a bounded catalog, support queues, workflow selection, a fast first stage before an LLM router; paraphrastic or multilingual inputs.
- For model selection, only when exemplars represent model suitability and candidates have measured outcome differences on the real workload.

Do not use when:
- Exact rules already satisfy the requirement, or route distinctions are not semantically expressible.
- It would be the sole decision-maker for numeric constraints, exact identifiers, negation-sensitive policy, code syntax or rare high-impact actions.
- The system cannot support a none-of-the-above outcome, required languages or domains fail local tests, or the exemplar corpus cannot be retained and governed.

Design notes:
- Representation: direct description matching (one rich definition per route; the wording is a single point of failure), or exemplar matching scored by maximum similarity, one or several centroids per route, or class-balanced k-nearest-neighbour voting; test these against the same frozen data rather than assuming one. Use hybrid dense and lexical retrieval when exact tokens and meaning both matter, fused after eligibility filters.
- Exemplars: cover the distinct semantic modes, languages and lengths of each route; keep hard negatives from the nearest competing routes; balance route representation so a route with more examples does not win by volume; keep duplicates and one conversation family inside one data split; record provenance for synthetic examples and never let them validate themselves.
- Accept a route only with absolute evidence and separation: its calibrated score meets its threshold, the margin to the second route meets a configured margin, it has enough neighbour support, and no policy or anomaly gate blocks it. Similarity is not probability; softmax over similarities is not an unknown detector.
- Very short queries, identifiers and keyword commands lack semantics: resolve trusted conversation state, use exact or lexical features, and abstain when the input stays underspecified.
- Keep the authoritative route registry outside the vector index; the index is a derived artifact. Avoid approximate nearest-neighbour indexing until exact search fails a measured service objective.

## LLM-based routing

Use when all of these are substantially true:
- Inputs are natural language, multimodal, context-dependent or too nuanced for a stable rule set.
- Downstream capabilities, risk levels, costs or service objectives genuinely differ.
- A wrong route can be detected, recovered from or sent to a safe default.
- The added routing call fits the latency and cost budget.
- Labelled or reviewable traffic exists for evaluation.
- Route definitions and execution permissions can be separated.

Do not use when:
- A short deterministic rule, authenticated metadata field, API path or user choice already identifies the destination, or a reliable classifier already does the job.
- The latency budget is tighter than a routing inference plus dispatch overhead.

Design notes:
- The router selects only among supplied route identifiers, under a schema with an enum; keep the output small and request no hidden reasoning. Use constrained structured output when supported.
- Write the router prompt as a classification policy: trusted policy and route definitions before clearly delimited untrusted content; each route by inclusion criteria, exclusions and decisive evidence; precedence for overlapping routes; clarify, abstain, deny and human review as first-class outcomes; whether several routes are allowed and the maximum; boundary, near-miss, adversarial, multi-intent and out-of-scope examples. Keep temperature low, but low temperature is neither determinism nor calibration.

## Capability routing

Use when:
- Handlers differ in material abilities and requests impose requirements that can be represented and checked: modality, language, context length, tool access, data format, domain qualification, side-effect class, latency, cost, region, compliance, availability, demonstrated task performance.
- The candidate catalog changes independently of the router, clients discover agents or tools dynamically, or one intent can be served by several handlers with different operating envelopes.
- A wrong assignment can be detected or contained, the catalog has accountable owners, and declarations have freshness and evidence.

Do not use when:
- Trusted metadata or policy already determines the route; a capability router considers only candidates that survive those gates.
- Declarations cannot be kept current, owners will not accept responsibility for them, a small rule set is clearer, dispatch overhead exceeds the work, or every candidate must be tried anyway.
- High-impact work would be routed from self-description alone, or a flat keyword or embedding match would decide exact numeric limits, permission scopes, residency, certifications or irreversible effects.
- The system cannot express a no-qualified-candidate result.

Design notes:
- Build a typed requirement object first, separating user-supplied facts, authenticated context, inferred requirements, defaults and unresolved requirements; an inferred value never overrides trusted metadata.
- Split constraints into hard constraints (all must pass), soft preferences (rank only the candidates that passed) and unknowns (neither pass nor fail; a hard requirement with unknown evidence normally disqualifies or triggers clarification, verification or review). Evaluate exact constraints before semantic ones and policy before cost or quality; a high utility score never compensates for a failed hard constraint.
- Rank the qualified set by an explicit weighted utility (versioned weights; no policy hidden in a weight), lexicographic tiers, or a Pareto front with a controlled tie-break. Tie-break deterministically with a versioned order such as fresher evidence, stronger demonstrated quality, lower expected total cost, lower tail latency, lower load, then stable identifier.
- Choose the capability contract first, then a healthy instance. Capability is not authorization: re-authorize after selection and give the selected handler a short-lived, least-privilege credential for the approved operation only.
- When no candidate qualifies: clarify missing requirements, retry discovery once if the registry is stale, use an equivalent healthy deployment, offer an approved degradation, plan a bounded composition, queue for a human, or abstain, in that order; never silently ignore a failed constraint.

## Combining families

Most production systems are hybrid, in this order:
1. Deterministic policy, tenancy, authorization and modality gates.
2. An exact-cache decision when the complete routing context matches.
3. A fast rule, embedding router or classifier for high-confidence common cases.
4. An LLM router for the ambiguous middle.
5. Clarify, abstain, escalate or a safe default when uncertainty or risk remains.
6. A provider gateway selects a healthy deployment only after the semantic route and policy constraints are known.

Other arrangements:
- Supervised classifier: when traffic is high, labels are stable and enough representative data exists; it brings retraining, calibration and drift obligations.
- Learned quality or cost router: only when training labels are actual candidate-model outcomes, not vague complexity labels; re-evaluate when models, prices, prompting or traffic change.
- Cascade: start with a cheaper or faster handler and escalate when its answer or confidence is inadequate; use it when weak-model results can be scored cheaply enough to decide whether to continue, and count latency and spend from every attempted stage.
- Mixture of agents: invoke several handlers and aggregate only for task types where parallel diversity has measured value; it multiplies cost, latency and attack surface.
