---
created: "2026-11-04T23:17:47Z"
updated: "2026-11-04T23:17:47Z"
---

# Reflection record: fields, values and invariants

Used for Part 3 (Reflection schema). The schema is closed and versioned, with every decision-relevant field required; optional free text is short and bounded. Each row below becomes one row of the Part 3 table (Field, Type or values, Rule).

## Fields

| Field | Type or values | Rule |
|---|---|---|
| Identity | reflection_id, schema_version, trace_id, span_id, task_id, attempt_id, candidate_id, parent_reflection_id, trigger_event_id | All required; links the record to its trace and candidate. |
| Subject | subject_type: plan, tool_result, proposed_action, draft_answer, code_patch, retrieval_set, final_candidate; subject_digest; immutable reference | The digest is content-addressed; evidence must carry the same digest. |
| Trigger | trigger_type (values as in Part 2) | Set by the orchestrator, not the model. |
| Applicable requirements | versioned requirement or policy IDs, user-constraint IDs, acceptance-criterion IDs, risk class | IDs only; no pasted policy corpus. |
| Verdict | pass, pass_with_warnings, revise, gather_evidence, escalate, block, abstain | No generic boolean: uncertainty and missing evidence differ from failure. |
| Defects | bounded array; each item: defect_id, category, severity, affected span or artifact reference, short description, requirement ID, evidence references, confidence, proposed correction, status | Array length capped. |
| Defect category | factual_error, logical_error, unsupported_claim, citation_mismatch, requirement_omission, policy_violation, authorization_missing, security_risk, privacy_risk, schema_error, tool_error, stale_data, test_failure, inconsistency, ambiguity, unsafe_side_effect, cost_or_budget_risk, unknown | Minimum taxonomy; extend by versioning. |
| Severity | critical, high, medium, low, informational | Needs organizational definitions. A critical defect blocks; an informational one never forces revision by itself. |
| Evidence | per item: evidence_id, evidence type, producer, immutable artifact reference, content digest, creation time, trust tier, relevant span or test name, freshness time, verification status | Text from an untrusted tool remains data, not instruction. |
| Coverage | checked requirement IDs, unchecked requirement IDs, reason each was not checked | A pass with an unchecked critical requirement is invalid. |
| Confidence | probability from 0 to 1 that this verdict is correct under the stated ground-truth rule; calibration_profile_id; confidence method; abstention reason when unsupported | One event only (see the calibration plan). |
| Uncertainty | epistemic uncertainty, missing evidence, conflicting evidence, verifier uncertainty | Kept separate, not one narrative score. |
| Next action | continue, revise_candidate, rerun_verifier, gather_specific_evidence, replan, call_stronger_critic, request_human_review, rollback, terminate; target IDs and bounded parameters | Required. |
| Stop decision | continue or stop; stop_reason; current and maximum iteration counts; remaining token and time budgets; escalation required | stop_reason is machine-checkable. |
| Change hypothesis | defect addressed, expected measurable effect, verifier to rerun | Required for revise. |
| Summary | short assessment for human review | No hidden-reasoning request, no unbounded scratchpad. |
| Provenance | model provider, exact model snapshot, reasoning setting, prompt version and digest, tool-definition digest, sampling configuration, critic role, timestamps | Required. |

## Invariants (enforced in application code, not only by type)

- pass: no unresolved critical or high defect, no missing critical requirement, all configured mandatory verifiers passing.
- pass_with_warnings: every warning is non-blocking and tied to a documented risk-acceptance rule.
- revise: at least one actionable defect, a target candidate, a change hypothesis and a verifier to rerun.
- gather_evidence: the missing evidence is named and a permitted retrieval or verification action exists.
- escalate: a destination class and an escalation reason.
- block: a policy, security, authorization or unrecoverable-correctness reason.
- abstain: mandatory when the reflector cannot evaluate the subject with the available evidence; never coerced into pass or fail.
- A confidence value without a compatible calibration profile is advisory only.
- Evidence references must resolve and their digests must match before a verdict is consumed; unresolved references are rejected before any transition.
- The reflector may not set approval, authorization, user-consent or policy-engine fields.

Schema-constrained decoding improves syntax and loggability but cannot make claims true: validate the record again in code, reject unknown fields, cap arrays and strings, keep an explicit refusal path. Never silently redefine pass; version taxonomies and enum meanings.

If the target provider or framework cannot preserve the required enums, evidence identifiers, refusal handling, schema version, call correlation or a mandatory approval pause, that integration cannot carry the record. Define one canonical record and compile it to each provider's tool schema or structured response format.

## Example of a revise record (format only)

```text
verdict: revise
subject_type: code_patch    candidate_id: c-17    subject_digest: <digest of c-17>
defects:
  - defect_id: d-1  category: schema_error  severity: high
    requirement ID: req-output-columns  evidence references: ev-3 (validator run on c-17)
    proposed correction: rename column order_ts to ordered_at   status: open
coverage: checked req-output-columns, req-null-rules; unchecked none
confidence: 0.7  calibration_profile_id: none (advisory only)
next action: revise_candidate  target: c-17
change hypothesis: fixes d-1; expected effect: validator error count drops to zero; rerun: schema validator
stop decision: continue; iteration 1 of 2
```
