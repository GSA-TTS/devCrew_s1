---
created: "2026-11-04T20:13:49Z"
updated: "2026-11-04T20:22:04Z"
---

# WCAG 2.1 levels, principles and the minimum sweep

## Conformance levels

Each level includes everything in the levels below it.

- Level A (minimum): text alternatives for non-text content; captions for prerecorded audio and video; all functionality available from the keyboard; no time limits, or time limits the user can adjust; no flashing content that can cause seizures; skip navigation links; page titles that describe the topic; logical focus order; link purpose clear from the link text.
- Level AA, in addition to A: captions for live audio; audio descriptions for video; contrast of 4.5:1 for normal text and 3:1 for large text; text resizable up to 200% without loss of content; actual text instead of images of text; consistent navigation across pages; consistent identification of components.
- Level AAA, in addition to AA: sign language interpretation for videos; extended audio descriptions; no background audio in speech recordings; contrast of 7:1 for normal text; text spacing adjustable without loss; no images of text (limited exceptions); context-sensitive help; error prevention for legal and financial transactions. AAA is hard to reach for all content and is often applied only to critical sections.

## The four principles and their guidelines

The first digit of a success criterion number is its principle. The Level column of a violation row takes the level given for the criterion here or in the fix patterns: 3.3.1 error identification and 3.3.2 labels for form inputs are Level A.

| Principle | Guidelines | Example success criteria (level) |
|---|---|---|
| 1 Perceivable: information and components can be perceived | 1.1 Text Alternatives; 1.2 Time-based Media (captions, audio descriptions, transcripts); 1.3 Adaptable (works in different presentations); 1.4 Distinguishable (easy to see and hear) | 1.1.1 (A) images have alt attributes; 1.3.1 (A) information conveyed through structure such as headings and lists; 1.4.3 (AA) text contrast at least 4.5:1; 1.4.11 (AA) non-text contrast at least 3:1 for UI components |
| 2 Operable: components and navigation can be operated by all users | 2.1 Keyboard Accessible; 2.2 Enough Time; 2.3 Seizures (nothing flashes more than 3 times per second); 2.4 Navigable; 2.5 Input Modalities | 2.1.1 (A) every interactive element works from the keyboard; 2.1.2 (A) no keyboard trap; 2.4.1 (A) skip navigation link; 2.4.3 (A) logical focus order; 2.5.3 (A) label in name matches the visible text |
| 3 Understandable: information and operation can be understood | 3.1 Readable; 3.2 Predictable; 3.3 Input Assistance | 3.1.1 (A) page language set in the HTML; 3.2.1 (A) focus causes no unexpected change of context; 3.2.3 (AA) consistent navigation; 3.3.1 (A) error messages identify what is wrong; 3.3.2 (A) labels for form inputs |
| 4 Robust: works with current and future technologies, including assistive technology | 4.1 Compatible | 4.1.1 (A) valid HTML, no duplicate IDs, proper nesting; 4.1.2 (A) name, role and value available for every UI component; 4.1.3 (AA) status messages exposed to assistive technology |

## Minimum sweep (run on every audit)

1. All images have alt text.
2. Colour contrast at least 4.5:1.
3. All form inputs have labels.
4. Everything works from the keyboard, with no mouse.
5. Focus indicators are visible.
6. No keyboard traps.
7. Page language is specified.
8. Heading structure is logical (h1, h2, h3).
9. Link text is descriptive (not click here).
10. Error messages are clear and helpful.
11. Time limits can be adjusted or extended.
12. No audio plays automatically.
13. No content flashes 3 or more times per second.
14. Content works at 200% zoom.
15. HTML is valid.

## Level named by law (when the user gives a jurisdiction)

As of: undated; the newest date in the material it was taken from is 2021, so a law's current level may differ.

| Law | Applies to | Standard it references |
|---|---|---|
| ADA (United States) | businesses, government, public accommodations | WCAG 2.1 Level AA (Department of Justice guidance) |
| Section 508 (United States) | federal agencies and contractors; mandatory for federal procurement | WCAG 2.0 Level AA (2017 update) |
| EN 301 549 (European Union) | public sector websites and apps | WCAG 2.1 Level AA |
| AODA (Ontario, Canada) | Ontario businesses and organizations | WCAG 2.0 Level AA |
| DDA (Australia) | all organizations; enforcement is complaint-based | WCAG 2.1 Level AA recommended |
