---
created: "2026-11-04T20:13:49Z"
updated: "2026-11-04T20:13:49Z"
---

# Common violations and their fixes

Each entry gives the criterion, what the violation looks like in the markup and the fix to write in the Fix column.

## 1.1.1 Non-text Content (A): missing alt text

- Violation: an img element with no alt attribute, or an informative image (a chart, a logo) with an empty alt.
- Fix: informative image, alt text that states its purpose (the company name for a logo; for a chart, what it shows, such as the trend and its size). Decorative image, alt="" with role="presentation".
- Alt text rules: describe the purpose, not only the appearance; keep it under 125 characters; do not start with image of or picture of; an empty alt is correct only for a decorative image.

## 1.4.3 Contrast (Minimum) (AA): low text contrast

- Violation: text or button colours whose ratio against the background is below 4.5:1 for normal text (3:1 for large text).
- Fix: darken the foreground or change the background until the pair reaches 4.5:1 (7:1 when the target is AAA); state the old and new colour values and the ratio of each.
- Check the ratio with a contrast checker, such as the one in the browser's developer tools.

## 3.3.2 Labels or Instructions (A): missing form labels

- Violation: an input whose only label is its placeholder, or no label at all.
- Fix: a visible label element whose for attribute matches the input's id (preferred). When the design cannot show a label, keep a label element hidden visually with a screen-reader-only class (absolutely positioned, 1px by 1px, clipped, overflow hidden), so assistive technology still reads it.

## 2.1.1 Keyboard (A): elements that work only with a mouse

- Violation: a div or span with an onclick handler acting as a button, menu or dropdown.
- Fix: use a native button element. If a custom element must stay, add role="button", tabindex="0" and a keydown handler that runs the same action on Enter and Space and prevents the default action of Space.

## 3.1.1 Language of Page (A): missing page language

- Violation: an html element with no lang attribute.
- Fix: set lang on the html element (lang="en" for English); mark any passage in another language with its own lang attribute on its element.

## 2.4.3 Focus Order (A): inaccessible modal dialogs

- Violation: a modal built from plain div elements with no role, no accessible name and no focus handling.
- Fix: give the container role="dialog", aria-modal="true" and aria-labelledby pointing to the dialog's heading. On open, save the element that had focus and move focus to the first focusable element in the dialog; keep Tab and Shift+Tab cycling inside the dialog (from the last element back to the first, and the reverse); close on Escape; on close, return focus to the saved element.

## 2.2.1 Timing Adjustable (A): time limits without warning

- Violation: a session that ends after a fixed time with no warning.
- Fix: warn the user before the limit (for a 5-minute limit, warn at 4 minutes) and offer to extend; on extension, clear both timers and restart them.
