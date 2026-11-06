---
created: "2026-11-04T20:13:49Z"
updated: "2026-11-04T20:13:49Z"
---

# What markup can show, and the manual tests for the rest

## Confirmable from markup or an automated scan

Automated checks cover about 30 to 40% of WCAG criteria: missing alt text, colour contrast, form labels, HTML validity, ARIA attributes, heading structure and link text. A code review of supplied markup can confirm the same kinds of findings. The other 60 to 70% need a person to test.

## Manual tests

Write each test that applies to the audited material, with the criteria it covers.

1. Keyboard navigation (2.1.1, 2.1.2, 2.4.3): put the mouse aside; Tab through every interactive element; confirm each focus indicator is visible; check for keyboard traps; try any keyboard shortcuts.
2. Screen reader (1.3.1, 2.4.6, 4.1.2): test with NVDA (Windows, free), JAWS (Windows, commercial), VoiceOver (macOS and iOS, built in) or TalkBack (Android, built in).
3. Zoom and reflow (1.4.4, 1.4.10): zoom the browser to 200%; confirm there is no horizontal scrolling and the text reflows; test on mobile viewport sizes.
4. Colour and contrast (1.4.1, 1.4.11): view the page in grayscale; confirm no information is carried by colour alone; check with a colour-blindness simulator.
5. Forms (3.3.1, 3.3.2, 3.3.3, 3.3.4): submit the form with errors; confirm the error messages are clear; test inline validation; check that the user can recover from each error.

Browser extensions such as axe DevTools, WAVE, Lighthouse (built into Chrome DevTools) and Accessibility Insights run the automated checks.
