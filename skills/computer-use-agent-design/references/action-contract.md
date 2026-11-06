---
created: "2026-11-04T23:17:26Z"
updated: "2026-11-04T23:17:26Z"
---

# Action contract

Used for Part 3 (Action contract table: Action, Parameters and limits, Side-effect class, Verification rule, Approval class).

## Action column: which actions to expose

Expose only the actions the task class needs. A useful set: screenshot, inspect region, move, left click, right click when justified, double click, type literal text, press a bounded shortcut, scroll, drag along a validated path, wait for a condition, switch a known tab or window, open an approved URL, upload an approved artifact, download into quarantine.

Do not expose unrestricted shell shortcuts, clipboard reads or history, browser developer tools, password-manager UI, extension installation, arbitrary URL schemes, local file navigation, local-network destinations or OS administration, unless the task explicitly needs one and a stronger isolation and approval profile applies.

## Parameters and limits column

Define per action: allowed parameters, coordinate space, maximum text bytes, approved keys, maximum scroll delta, maximum drag length, target window and timeout. Action-specific rules:

- Click: single click for buttons, links, checkboxes, focus and selection. Double click only when the application requires it; verify the target before both clicks and bound the inter-click timing in the adapter.
- Type: prefer a semantic fill for web form fields, since it targets a labelled field and can verify its value; simulated keystrokes only where a control needs them. Clear a field only after confirming the target, its current value and whether clearing is reversible. Model-generated text is untrusted output: validate length, format, recipients, amount, date, locale and prohibited content before typing.
- Shortcut: an allowlist per OS and application; normalize key names and reject unknown modifiers. Shortcuts carry more authority than typing (they can escape the application, open developer tools, close unsaved work); never send a global shortcut to an unfocused or unknown window.
- Scroll: inside a known container or at a verified coordinate, in bounded increments; record offsets where accessible; avoid repeated full-page jumps without a stable landmark.
- Wait: a named condition (element visible, URL changed, spinner gone, download complete, dialog present, animation stable, state hash unchanged across two samples). A fixed sleep only when the interface has no observable signal, capped and followed by verification. Network idle is not a universal success condition.
- Drag: only when no semantic alternative exists; validate every path point, start and end targets, hazards in between, distance and window; take a fresh screenshot just before and after.
- Tabs, windows, dialogs: track each by a stable internal ID, title hash, origin or process, bounds, opener and last-seen time, never by visible title alone. A new tab, window, permission dialog, download prompt or native file chooser pauses ordinary actions for reorientation. Allow pop-ups only from approved origins; reject unexpected requests for camera, microphone, location, notifications, clipboard, filesystem, protocol handlers or extensions. Native file dialogs receive only broker-selected paths.
- Upload: references an application-controlled artifact ID that a broker resolves to a read-only file after authorization, malware scan, type and size checks, data classification and destination policy. The model never browses the host filesystem.
- Download: lands in a task-specific quarantine directory with URL and redirect chain, requested and detected type, size, hash, scan result and safe storage name recorded; it is never opened in the same privileged session.

## Side-effect class column

One of: public read, private read, reversible local edit, external communication, financial, identity or permission change, destructive, privileged, arbitrary execution.

## Verification rule column

Name deterministic evidence where it exists: locator value, URL and origin, application state, file hash, database or API record, sent-item ID, transaction ID, or an execution-based evaluator. Use visual verification only for visual claims, and name the specific region or feature to check; a model's statement that the screen looks right is not verification.
