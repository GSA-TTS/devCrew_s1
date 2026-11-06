---
created: "2026-11-04T20:13:49Z"
updated: "2026-11-04T20:22:04Z"
---

# Conformance summary (Accessibility Conformance Report) and score

## Report parts

An Accessibility Conformance Report (ACR), also known as a VPAT (Voluntary Product Accessibility Template), has these parts, in this order:

1. Header: Product, Version, Report Date (YYYY-MM-DD), Conformance Level (A, AA or AAA).
2. Summary: one line naming the WCAG 2.1 level and the number of known issues. The line says Conforms only when every criterion of the target level is Supports; otherwise it says Evaluated against the level and gives the counts of known issues and of criteria not evaluated.
3. Success Criteria table: Criterion (number and name), Level, Conformance, Remarks.
4. Known Issues: a numbered list, one entry per issue, titled with the issue and its criterion number, each with Impact, Affected pages, Remediation and ETA.

Conformance values: Supports, Partially Supports, Does Not Support, Not Evaluated.

## Format example

```markdown
# Accessibility Conformance Report

Product: Riverside Library room booking
Version: 2.3
Report Date: 2026-10-12
Conformance Level: AA

## Summary
Evaluated against WCAG 2.1 Level AA: 2 known issues, 1 criterion not evaluated.

## Success Criteria
| Criterion | Level | Conformance | Remarks |
|---|---|---|---|
| 1.1.1 Non-text Content | A | Supports | Confirmed in markup: every room photo has alt text |
| 1.4.3 Contrast (Minimum) | AA | Partially Supports | Date picker hint text below 4.5:1 |
| 2.1.1 Keyboard | A | Not Evaluated | Needs the keyboard navigation test |
| 3.3.1 Error Identification | A | Partially Supports | Booking error names no field |

## Known Issues
1. Low contrast on date picker hints (1.4.3)
   - Impact: Medium
   - Affected pages: room booking
   - Remediation: darken the hint text until it reaches 4.5:1
   - ETA: to be set by the team
2. Error message does not name the field (3.3.1)
   - Impact: High
   - Affected pages: room booking, booking confirmation
   - Remediation: name the field and the problem in the message
   - ETA: to be set by the team
```

## Accessibility score (only when asked)

- Score = 100 - (weighted violations / total checks x 100).
- Weights: Critical 10 points each, High 5, Medium 2, Low 1.
- Grades: A+ 95 to 100 (excellent, minimal issues); A 90 to 94 (very good, minor issues); B 80 to 89 (good, some improvements needed); C 70 to 79 (fair, significant improvements needed); D 60 to 69 (poor, major barriers); F below 60 (failing, critical issues).
