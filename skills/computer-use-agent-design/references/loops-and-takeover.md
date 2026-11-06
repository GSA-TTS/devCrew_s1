---
created: "2026-11-04T23:17:26Z"
updated: "2026-11-04T23:17:26Z"
---

# Loops, budgets, approval and takeover

Used for Part 4 (Loops and budgets: Loop, Enters when, Exits, Budget) and Part 5 (Approval and takeover: Trigger, Handling, What the user sees).

## Starting budgets

For an ordinary interactive task: at most 30 actions, 20 screenshots, 10 model turns, two recovery cycles, two approval prompts and five minutes of active runtime. Lower them for side effects. Budgets are enforced outside the model.

## The six loops

Perceive-decide-act-verify
- Enters when: the environment is oriented, an unsatisfied subgoal remains, and action, time and cost budgets remain.
- Steps: perceive (fresh observation with an ID; reject it if dimensions, transform, state version, URL, active target or timestamp are inconsistent); decide (one atomic action, with intended target, expected local postcondition, risk class and verifier); ground (abstain and inspect if confidence is insufficient); authorize in deterministic code (parameters, identity, destination, data release, state precondition, policy, approval, budgets); act through the adapter with a deadline, never a partial streamed action; settle; verify; checkpoint after a verified meaningful state, before a risky transition and before an approval or takeover.
- Exits: success when all task-level postconditions pass; stop on user cancellation, policy denial, required takeover, unrecoverable state, repeated state, exhausted budget, security signal or unknown consequential outcome.
- Budget: the starting budgets. One action per observation by default; at most three batched actions, only when they are deterministic, low risk, in one stable field or region, and none can change layout or navigation. Never batch across submit, navigation, download, upload, modal, external communication, permission, payment or destructive boundaries.

Wait-and-settle
- Enters when: after navigation, click, type, upload, download, app launch, tab switch, dialog response, or any action whose effect may be asynchronous.
- Steps: name the condition and an absolute deadline first; poll a semantic condition when available, otherwise compare a stable-region hash, spinner state or target geometry at bounded intervals; where animation or streaming matters, require stability across two consecutive samples.
- Exits: success when the condition holds and the target is still valid; to recovery on a known error, unexpected dialog, origin change or stale target; timeout otherwise. A timeout is not converted into another click.
- Budget: at most five polls or the action-specific deadline, whichever comes first.

Verification
- Enters when: after every action and before every completion claim.
- Steps: compare the observed state with the declared local postcondition, using the evidence named in the action's Verification rule.
- Exits: verified when mandatory checks pass; to recovery on a known wrong state; unknown and escalate for a consequential action when authoritative state cannot show whether it happened. The action is never repeated only because a success screen is missing.
- Budget: one additional observation after settling if the postcondition is absent but state is safe; one alternate verifier (DOM plus screenshot, API plus UI) if evidence is ambiguous.

Recovery and reorientation
- Enters when: wrong page, lost focus, stale element, unexpected dialog, failed click, navigation error, changed layout, crash, tab confusion, or verification failure without a security signal.
- Steps: stop acting; take a full fresh observation; compare with the last verified checkpoint; try the least destructive recovery (dismiss a known harmless overlay, restore the known tab, an application-supported back action, reload a read-only page, rebuild from the checkpoint); recompute every coordinate and locator; re-evaluate policy, approvals and budgets. Repeated back, refresh or Escape is not a generic recovery: it can resubmit forms, lose work or accept unsafe defaults.
- Exits: success when the state is recognized, the next subgoal is valid and a fresh checkpoint is written; immediate human takeover if data could be lost, a session may be compromised or a consequential outcome is unknown; after two unsuccessful attempts, human takeover, and failed when no takeover is available or the person does not restore a recognized state.
- Budget: two recovery cycles for an interactive task; a durable workflow may restore once into a fresh environment from an approved checkpoint.

Stuck and oscillation
- Enters when: after every verified or failed step.
- Steps: compute a state signature (subgoal, normalized URL or application, active target, screenshot perceptual hash, DOM or accessibility summary hash, focused element, last action and target, progress markers); count no-progress steps; detect exact repeats and two or three signatures alternating without progress. Animation, ads, clocks or cursors changing the screenshot bytes do not reset the counters; use task-relevant masked regions.
- Exits: reorientation after three no-progress steps or the first repeated action-state pair; stop and escalate after one failed reorientation, two repeats of the same signature or five total no-progress steps.
- Budget: the counts in Exits.

Approval and takeover
- Enters when: a trigger in the next section occurs.
- Steps: pause the environment and block model input; create an approval request with an operation hash over user, tenant, account, exact target, action, values, recipient or destination, disclosed data, files, origin, model and tool version, screenshot hash, state version and expiry; present the preview; on denial or expiry do not execute, record it, and terminate or choose a materially different safe plan; a user edit creates a new proposal and hash, never a changed approved request; on return clear secret-bearing surfaces, restore capture, raise the state version, take a fresh observation and re-run policy and state checks before executing.
- Exits: execute after approval and fresh checks; stop after a second denial or expiry of the same intent.
- Budget: at most one revised approval request for the same intent.

## Approval and takeover triggers (Trigger column)

External communication, purchase, payment, agreement, acceptance of legal terms, deletion, account or permission change, sensitive upload, production change, warning bypass, CAPTCHA, credential entry, any action the provider or application requires confirmation for, and any destructive, submit, publish, send, grant, install or download control.

## Handling column

- Approval: the user approves an exact operation preview before execution.
- Exclusive takeover: for credentials, payment details, one-time codes, passkeys and CAPTCHA. The user gets exclusive input control, model-visible capture is suppressed, keystrokes are not recorded, the control state is shown visually, and control ends on explicit release or timeout. CAPTCHA is an access-control signal, handed to the user only where the service permits human completion, never solved by the model, a solving service or a hidden endpoint.

## What the user sees column

The exact action, material values, data disclosure, side effects, reversibility, uncertainty and a current redacted preview.
