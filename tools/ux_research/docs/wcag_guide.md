# WCAG 2.1 Compliance Guide

Understanding Web Content Accessibility Guidelines (WCAG) 2.1 and implementing
compliant web experiences.

## Table of Contents

- [What is WCAG?](#what-is-wcag)
- [WCAG Levels Explained](#wcag-levels-explained)
- [Four Principles (POUR)](#four-principles-pour)
- [Common Violations and Fixes](#common-violations-and-fixes)
- [Testing Methodology](#testing-methodology)
- [Compliance Reporting](#compliance-reporting)
- [Legal Requirements](#legal-requirements)
- [Resources](#resources)

## What is WCAG?

Web Content Accessibility Guidelines (WCAG) 2.1 is an internationally recognized
standard for web accessibility developed by the World Wide Web Consortium (W3C).
It provides technical criteria for making web content accessible to people with
disabilities.

### Key Facts

- **Published**: June 2018 (extends WCAG 2.0 from 2008)
- **Status**: W3C Recommendation (official web standard)
- **Legal Basis**: Referenced in ADA, Section 508, EN 301 549, and many national laws
- **Scope**: Covers web pages, web applications, mobile apps, PDFs, and documents

### Who Benefits?

WCAG compliance helps users with:
- Visual disabilities (blindness, low vision, color blindness)
- Hearing disabilities (deafness, hard of hearing)
- Motor disabilities (limited dexterity, tremors)
- Cognitive disabilities (dyslexia, ADHD, autism)
- Seizure disorders (photosensitivity)
- Aging-related limitations

**Plus**: Better usability for everyone (keyboard users, mobile users, slow connections)

## WCAG Levels Explained

WCAG 2.1 defines three conformance levels, each building on the previous:

### Level A (Minimum)

**25 success criteria** - Most basic accessibility features

**Key Requirements:**
- Non-text content has text alternatives (alt text)
- Captions for prerecorded audio/video
- Keyboard-accessible functionality
- No time limits (or adjustable)
- No flashing content that causes seizures
- Skip navigation links
- Page titles describe topic
- Logical focus order
- Link purpose clear from text

**Target**: Legal minimum in most jurisdictions

**Effort**: 20-40 hours for typical website

### Level AA (Mid-range)

**38 total criteria** (includes all Level A + 13 additional)

**Key Requirements (additional to Level A):**
- Captions for live audio
- Audio descriptions for video
- 4.5:1 color contrast for normal text
- 3:1 color contrast for large text
- Text resizable up to 200% without loss of content
- Images of text avoided (use actual text)
- Consistent navigation across pages
- Consistent identification of components
- Error identification and suggestions
- Labels provided for inputs

**Target**: Industry best practice, recommended for most websites

**Effort**: 40-80 hours for typical website

### Level AAA (Highest)

**61 total criteria** (includes all AA + 23 additional)

**Key Requirements (additional to Level AA):**
- Sign language interpretation for videos
- Extended audio descriptions
- No background audio in speech recordings
- 7:1 color contrast for normal text
- Text spacing adjustable without loss
- No images of text (with limited exceptions)
- Context-sensitive help available
- Error prevention for legal/financial transactions

**Target**: Specialized sites (government, healthcare, education)

**Effort**: 80-160+ hours for typical website

**Note**: Level AAA is difficult to achieve for all content; often applied
selectively to critical sections.

## Four Principles (POUR)

WCAG is organized around four fundamental principles:

### 1. Perceivable

Information and UI components must be presentable to users in ways they can perceive.

**Guidelines:**
- **1.1 Text Alternatives**: Provide alt text for images
- **1.2 Time-based Media**: Captions, audio descriptions, transcripts
- **1.3 Adaptable**: Content works in different presentations (responsive)
- **1.4 Distinguishable**: Make content easy to see and hear

**Example Success Criteria:**
- 1.1.1 (A): All images have alt attributes
- 1.3.1 (A): Information conveyed through structure (headings, lists)
- 1.4.3 (AA): Color contrast ratio of at least 4.5:1
- 1.4.11 (AA): Non-text contrast of at least 3:1 for UI components

### 2. Operable

UI components and navigation must be operable by all users.

**Guidelines:**
- **2.1 Keyboard Accessible**: All functionality via keyboard
- **2.2 Enough Time**: Users have enough time to read and use content
- **2.3 Seizures**: No content that flashes more than 3 times per second
- **2.4 Navigable**: Help users navigate and find content
- **2.5 Input Modalities**: Make it easier to operate via various inputs

**Example Success Criteria:**
- 2.1.1 (A): All interactive elements keyboard accessible
- 2.1.2 (A): No keyboard trap (focus can move away)
- 2.4.1 (A): Skip navigation link provided
- 2.4.3 (A): Focus order is logical and intuitive
- 2.5.3 (A): Label in name matches visible text

### 3. Understandable

Information and operation of UI must be understandable.

**Guidelines:**
- **3.1 Readable**: Make text readable and understandable
- **3.2 Predictable**: Web pages appear and operate predictably
- **3.3 Input Assistance**: Help users avoid and correct mistakes

**Example Success Criteria:**
- 3.1.1 (A): Page language specified in HTML
- 3.2.1 (A): Focus doesn't cause unexpected context changes
- 3.2.3 (AA): Navigation is consistent across pages
- 3.3.1 (A): Error messages identify what's wrong
- 3.3.2 (A): Labels provided for form inputs

### 4. Robust

Content must be robust enough to work with current and future technologies.

**Guidelines:**
- **4.1 Compatible**: Maximize compatibility with assistive technologies

**Example Success Criteria:**
- 4.1.1 (A): HTML is valid (no duplicate IDs, proper nesting)
- 4.1.2 (A): Name, role, value available for all UI components
- 4.1.3 (AA): Status messages available to assistive tech

## Common Violations and Fixes

### Missing Alt Text (1.1.1 - Level A)

**Violation:**
```html
<img src="logo.png">
<img src="chart.png" alt="">
```

**Fix:**
```html
<!-- Informative images -->
<img src="logo.png" alt="Company Name Logo">

<!-- Complex images -->
<img src="chart.png" alt="Sales trend chart showing 20% growth">

<!-- Decorative images -->
<img src="divider.png" alt="" role="presentation">
```

**Best Practices:**
- Describe the image's purpose, not just appearance
- Keep alt text under 125 characters
- Don't use "image of" or "picture of"
- Use `alt=""` for decorative images

### Insufficient Color Contrast (1.4.3 - Level AA)

**Violation:**
```css
/* Contrast ratio: 3.2:1 (fails AA) */
.text {
  color: #777777;
  background-color: #ffffff;
}

.button {
  color: #999999;
  background-color: #ffffff;
}
```

**Fix:**
```css
/* Contrast ratio: 4.6:1 (passes AA) */
.text {
  color: #595959;
  background-color: #ffffff;
}

/* Contrast ratio: 7.4:1 (passes AAA) */
.button {
  color: #333333;
  background-color: #ffffff;
}
```

**Testing Tools:**
- Chrome DevTools: Inspect > Contrast ratio
- WebAIM Contrast Checker: https://webaim.org/resources/contrastchecker/
- UX Research Platform: Automated contrast analysis

### Missing Form Labels (3.3.2 - Level A)

**Violation:**
```html
<input type="text" name="email" placeholder="Enter email">
<input type="password" name="password">
```

**Fix:**
```html
<!-- Visible labels (preferred) -->
<label for="email">Email Address:</label>
<input type="text" id="email" name="email">

<label for="password">Password:</label>
<input type="password" id="password" name="password">

<!-- Hidden labels (when design requires) -->
<label for="search" class="sr-only">Search</label>
<input type="text" id="search" placeholder="Search...">
```

**CSS for screen reader only:**
```css
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}
```

### Non-Keyboard Accessible Elements (2.1.1 - Level A)

**Violation:**
```html
<!-- Clickable div without keyboard support -->
<div onclick="openMenu()">Menu</div>

<!-- Custom dropdown -->
<span class="dropdown" onclick="toggleDropdown()">
  Options
</span>
```

**Fix:**
```html
<!-- Use button element -->
<button type="button" onclick="openMenu()">Menu</button>

<!-- Or add keyboard support to custom elements -->
<span
  class="dropdown"
  role="button"
  tabindex="0"
  onclick="toggleDropdown()"
  onkeydown="if(event.key==='Enter'||event.key===' '){toggleDropdown()}"
>
  Options
</span>
```

**JavaScript for keyboard support:**
```javascript
function handleKeyDown(event) {
  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault();
    toggleDropdown();
  }
}
```

### Missing Page Language (3.1.1 - Level A)

**Violation:**
```html
<!DOCTYPE html>
<html>
  <head>
    <title>My Page</title>
  </head>
```

**Fix:**
```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <title>My Page</title>
  </head>
```

**Multiple languages:**
```html
<html lang="en">
  <p>Welcome to our site.</p>
  <p lang="es">Bienvenido a nuestro sitio.</p>
  <p lang="fr">Bienvenue sur notre site.</p>
</html>
```

### Inaccessible Modal Dialogs (2.4.3 - Level A)

**Violation:**
```html
<div class="modal">
  <div class="modal-content">
    <p>Modal content</p>
    <button onclick="closeModal()">Close</button>
  </div>
</div>
```

**Fix:**
```html
<div
  class="modal"
  role="dialog"
  aria-modal="true"
  aria-labelledby="modal-title"
>
  <div class="modal-content">
    <h2 id="modal-title">Confirmation</h2>
    <p>Are you sure you want to delete this item?</p>
    <button onclick="closeModal()">Cancel</button>
    <button onclick="confirmDelete()">Delete</button>
  </div>
</div>
```

**JavaScript for focus management:**
```javascript
function openModal() {
  const modal = document.querySelector('.modal');
  const focusableElements = modal.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );
  const firstElement = focusableElements[0];
  const lastElement = focusableElements[focusableElements.length - 1];

  // Save current focus
  lastFocusedElement = document.activeElement;

  // Show modal
  modal.style.display = 'block';

  // Set focus to first element
  firstElement.focus();

  // Trap focus within modal
  modal.addEventListener('keydown', function(e) {
    if (e.key === 'Tab') {
      if (e.shiftKey && document.activeElement === firstElement) {
        e.preventDefault();
        lastElement.focus();
      } else if (!e.shiftKey && document.activeElement === lastElement) {
        e.preventDefault();
        firstElement.focus();
      }
    }
    if (e.key === 'Escape') {
      closeModal();
    }
  });
}

function closeModal() {
  const modal = document.querySelector('.modal');
  modal.style.display = 'none';

  // Restore focus
  if (lastFocusedElement) {
    lastFocusedElement.focus();
  }
}
```

### Timing Issues (2.2.1 - Level A)

**Violation:**
```javascript
// Auto-logout after 5 minutes, no warning
setTimeout(() => {
  logout();
}, 300000);
```

**Fix:**
```javascript
// Warn user and allow extension
let timeoutId;
let warningId;

function startTimer() {
  // Warn at 4 minutes
  warningId = setTimeout(() => {
    showWarning('Your session will expire in 1 minute. Extend?');
  }, 240000);

  // Logout at 5 minutes
  timeoutId = setTimeout(() => {
    logout();
  }, 300000);
}

function extendSession() {
  clearTimeout(warningId);
  clearTimeout(timeoutId);
  hideWarning();
  startTimer(); // Restart timer
}
```

## Testing Methodology

### Automated Testing

Use the UX Research Platform for automated WCAG audits:

```bash
# Full WCAG 2.1 AA audit
ux-tool audit --url https://example.com --wcag-level AA

# Test specific success criteria
ux-tool audit --url https://example.com \
  --rules "color-contrast,image-alt,label"

# Multi-page audit
ux-tool audit --url https://example.com \
  --max-pages 50 \
  --output-format html json
```

**Automated testing covers ~30-40% of WCAG criteria**, including:
- Missing alt text
- Color contrast
- Form labels
- HTML validity
- ARIA attributes
- Heading structure
- Link text

### Manual Testing

**Required for ~60-70% of WCAG criteria:**

1. **Keyboard Navigation** (2.1.1, 2.1.2, 2.4.3)
   - Unplug mouse
   - Tab through all interactive elements
   - Verify visible focus indicators
   - Check for keyboard traps
   - Test keyboard shortcuts

2. **Screen Reader Testing** (1.3.1, 2.4.6, 4.1.2)
   - NVDA (Windows, free)
   - JAWS (Windows, commercial)
   - VoiceOver (macOS/iOS, built-in)
   - TalkBack (Android, built-in)

3. **Zoom/Reflow Testing** (1.4.4, 1.4.10)
   - Zoom to 200% (browser zoom)
   - Verify no horizontal scrolling
   - Check text reflow
   - Test on mobile viewports

4. **Color/Contrast** (1.4.1, 1.4.11)
   - Remove color (grayscale test)
   - Verify information not conveyed by color alone
   - Test with color blindness simulators

5. **Forms** (3.3.1, 3.3.2, 3.3.3, 3.3.4)
   - Submit forms with errors
   - Verify error messages are clear
   - Test inline validation
   - Check error recovery

### Testing Schedule

**Recommended frequency:**
- **Development**: Every sprint/iteration
- **Staging**: Before each release
- **Production**: Monthly monitoring
- **Major redesigns**: Full audit before and after

## Compliance Reporting

### Accessibility Conformance Report (ACR)

Also known as VPAT (Voluntary Product Accessibility Template).

**Structure:**
```markdown
# Accessibility Conformance Report

**Product**: [Your Website/App Name]
**Version**: [Version Number]
**Report Date**: [YYYY-MM-DD]
**Conformance Level**: [A, AA, or AAA]

## Summary
Conforms to WCAG 2.1 Level AA with [X] known issues.

## Success Criteria
| Criterion | Level | Conformance | Remarks |
|-----------|-------|-------------|---------|
| 1.1.1 Non-text Content | A | Supports | All images have alt text |
| 1.4.3 Contrast (Minimum) | AA | Partially Supports | 3 low-contrast elements identified, fixes scheduled |
| 2.1.1 Keyboard | A | Supports | All functionality keyboard accessible |
| ... | ... | ... | ... |

## Known Issues
1. **Low contrast on secondary buttons** (1.4.3)
   - Impact: Medium
   - Affected pages: All
   - Remediation: Update button styles
   - ETA: Sprint 23

2. **Missing form labels in checkout** (3.3.2)
   - Impact: High
   - Affected pages: /checkout
   - Remediation: Add explicit labels
   - ETA: Sprint 22
```

### Generate Reports with UX Platform

```bash
# Generate conformance report
ux-tool report \
  --audit audit-results.json \
  --output conformance-report.html \
  --format vpat

# Executive summary
ux-tool report \
  --audit audit-results.json \
  --output executive-summary.pdf \
  --format executive
```

### Scoring and Metrics

**Accessibility Score Calculation:**
```
Score = 100 - (weighted_violations / total_checks * 100)

Weights:
- Critical violations: 10 points each
- High violations: 5 points each
- Medium violations: 2 points each
- Low violations: 1 point each
```

**Example:**
```
Total checks: 150
Violations: 2 critical, 5 high, 10 medium, 15 low

Weighted = (2 * 10) + (5 * 5) + (10 * 2) + (15 * 1) = 80
Score = 100 - (80 / 150 * 100) = 46.7

Grade: F (Below 50)
```

**Grading Scale:**
- **A+ (95-100)**: Excellent, minimal issues
- **A (90-94)**: Very good, minor issues
- **B (80-89)**: Good, some improvements needed
- **C (70-79)**: Fair, significant improvements needed
- **D (60-69)**: Poor, major accessibility barriers
- **F (<60)**: Failing, critical accessibility issues

## Legal Requirements

### United States

**ADA (Americans with Disabilities Act)**
- Applies to: Businesses, government, public accommodations
- Standard: WCAG 2.1 Level AA (DOJ guidance)
- Penalties: $75,000-$150,000 fines, plus lawsuits

**Section 508**
- Applies to: Federal agencies and contractors
- Standard: WCAG 2.0 Level AA (updated 2017)
- Requirement: Mandatory for federal procurement

### European Union

**EN 301 549**
- Applies to: Public sector websites and apps
- Standard: WCAG 2.1 Level AA
- Deadline: September 2020 (existing), June 2021 (new)
- Penalties: Varies by member state

### Canada

**AODA (Accessibility for Ontarians with Disabilities Act)**
- Applies to: Ontario businesses and organizations
- Standard: WCAG 2.0 Level AA
- Deadline: 2021 (full compliance)

### Australia

**DDA (Disability Discrimination Act)**
- Applies to: All organizations
- Standard: WCAG 2.1 Level AA recommended
- Enforcement: Complaint-based

## Resources

### Official Standards

- **WCAG 2.1**: https://www.w3.org/TR/WCAG21/
- **Understanding WCAG**: https://www.w3.org/WAI/WCAG21/Understanding/
- **Techniques for WCAG**: https://www.w3.org/WAI/WCAG21/Techniques/

### Testing Tools

- **axe DevTools**: https://www.deque.com/axe/devtools/
- **WAVE**: https://wave.webaim.org/
- **Lighthouse**: Built into Chrome DevTools
- **UX Research Platform**: This tool

### Learning Resources

- **WebAIM**: https://webaim.org/
- **A11y Project**: https://www.a11yproject.com/
- **Deque University**: https://dequeuniversity.com/
- **Google Web Fundamentals**: https://developers.google.com/web/fundamentals/accessibility

### Screen Readers

- **NVDA** (free): https://www.nvaccess.org/
- **JAWS** (commercial): https://www.freedomscientific.com/products/software/jaws/
- **VoiceOver** (macOS): Built-in, Cmd+F5 to enable
- **TalkBack** (Android): Built-in

### Validator Extensions

- **axe DevTools** (Chrome/Firefox): Free browser extension
- **WAVE** (Chrome/Firefox/Edge): Free browser extension
- **Accessibility Insights** (Chrome/Edge): Microsoft's free tool

## Next Steps

1. Run automated audit: [Accessibility Testing Guide](accessibility_testing.md)
2. Implement fixes: Review [Common Violations](#common-violations-and-fixes)
3. Manual testing: Follow [Testing Methodology](#testing-methodology)
4. Generate reports: [Compliance Reporting](#compliance-reporting)
5. Continuous monitoring: Set up [CI/CD Integration](ci_cd_integration.md)

## Quick Reference Card

### Must-Have Checklist

- ✅ All images have alt text
- ✅ Color contrast 4.5:1 minimum
- ✅ All form inputs have labels
- ✅ Keyboard accessible (no mouse required)
- ✅ Visible focus indicators
- ✅ No keyboard traps
- ✅ Page language specified
- ✅ Heading structure logical (h1, h2, h3)
- ✅ Link text descriptive (not "click here")
- ✅ Error messages clear and helpful
- ✅ Time limits adjustable/extendable
- ✅ No auto-playing audio
- ✅ No flashing content (3+ flashes/sec)
- ✅ Responsive to 200% zoom
- ✅ Valid HTML (no errors)

Run this command for instant validation:
```bash
ux-tool audit --url https://your-site.com --wcag-level AA --quick-check
```
