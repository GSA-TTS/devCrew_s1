# Heuristic Evaluation Guide

Complete guide to usability evaluation using Nielsen's 10 heuristics and custom
checklists.

## Table of Contents

- [What is Heuristic Evaluation?](#what-is-heuristic-evaluation)
- [Nielsen's 10 Usability Heuristics](#nielsens-10-usability-heuristics)
- [Running Evaluations](#running-evaluations)
- [Custom Checklists](#custom-checklists)
- [Scoring Methodology](#scoring-methodology)
- [Recommendations](#recommendations)
- [Case Studies](#case-studies)
- [Best Practices](#best-practices)

## What is Heuristic Evaluation?

Heuristic evaluation is a usability inspection method where experts evaluate
a user interface against established principles (heuristics) to identify
usability problems.

**Key Benefits:**
- Quick and cost-effective
- Identifies 75-80% of major usability issues
- Can be performed early in design process
- Requires 3-5 evaluators for best results
- No users needed (expert-based)

**When to Use:**
- Early design phase (wireframes, mockups)
- Before usability testing
- After major redesigns
- Competitive analysis
- Periodic UX audits

## Nielsen's 10 Usability Heuristics

### 1. Visibility of System Status

**Principle:** Keep users informed about what is going on through appropriate
feedback within reasonable time.

**What to Check:**
- ✅ Loading indicators for async operations
- ✅ Progress bars for multi-step processes
- ✅ Status messages after user actions
- ✅ Current location indicators (breadcrumbs)
- ✅ Active state for selected items
- ✅ Real-time updates (if applicable)

**Good Example:**
```html
<!-- Clear progress indicator -->
<div class="upload-progress">
  <div class="progress-bar" style="width: 65%"></div>
  <span class="progress-text">Uploading... 65% (2.1 MB / 3.2 MB)</span>
  <span class="time-remaining">30 seconds remaining</span>
</div>
```

**Bad Example:**
```html
<!-- No feedback during long operation -->
<button onclick="processLargeFile()">Process</button>
<!-- User clicks and waits with no indication anything is happening -->
```

**Common Violations:**
- No loading indicator for operations >1 second
- Submit buttons don't show processing state
- No confirmation after important actions
- Unclear which tab/page is currently active

### 2. Match Between System and Real World

**Principle:** Speak the user's language with familiar words, phrases, and
concepts rather than system-oriented terms.

**What to Check:**
- ✅ Terminology matches user expectations
- ✅ Icons are intuitive and recognizable
- ✅ Information follows natural conventions
- ✅ Dates/times in familiar formats
- ✅ Currency in user's local format
- ✅ Metaphors align with real-world concepts

**Good Example:**
```html
<!-- Familiar e-commerce terms -->
<button class="add-to-cart">Add to Cart</button>
<button class="checkout">Proceed to Checkout</button>
<button class="save-for-later">Save for Later</button>
```

**Bad Example:**
```html
<!-- Technical jargon confusing to users -->
<button class="persist-entity">Persist Entity</button>
<button class="initiate-transaction-flow">Initiate Transaction Flow</button>
<div class="error">ERRNO 0x8007000E: Buffer overflow</div>
```

**Common Violations:**
- Technical error messages (error codes without explanation)
- Industry jargon not familiar to target audience
- Inconsistent terminology across the interface
- Icons that don't match user mental models

### 3. User Control and Freedom

**Principle:** Provide "emergency exits" to allow users to leave unwanted states
without extensive dialog.

**What to Check:**
- ✅ Undo/redo functionality
- ✅ Cancel buttons in dialogs
- ✅ Back button works as expected
- ✅ Easy way to exit modal dialogs (X, Esc key)
- ✅ Ability to pause/stop long operations
- ✅ Draft saving for forms

**Good Example:**
```html
<!-- Clear escape routes -->
<div class="modal">
  <button class="close" aria-label="Close">×</button>
  <h2>Delete Account</h2>
  <p>Are you sure? This action cannot be undone.</p>
  <button class="danger">Delete</button>
  <button class="cancel">Cancel</button>
</div>

<!-- Undo notification -->
<div class="notification">
  Email deleted. <button>Undo</button>
</div>
```

**Bad Example:**
```html
<!-- No way to cancel or go back -->
<div class="wizard">
  <h2>Step 3 of 5</h2>
  <!-- No back button, no cancel, must complete all steps -->
  <button class="next">Next</button>
</div>
```

**Common Violations:**
- No undo for destructive actions
- Modal dialogs without close button
- Multi-step wizards without back navigation
- No way to cancel long-running operations

### 4. Consistency and Standards

**Principle:** Follow platform conventions and maintain internal consistency.

**What to Check:**
- ✅ Consistent navigation across pages
- ✅ Same terminology for same actions
- ✅ Consistent button placement
- ✅ Standard UI component behavior
- ✅ Follows platform conventions (iOS, Android, Web)
- ✅ Color coding is consistent

**Good Example:**
```html
<!-- Consistent button styles and placement -->
<div class="form-actions">
  <button class="btn-primary">Save</button>
  <button class="btn-secondary">Cancel</button>
</div>

<!-- Used consistently across all forms -->
```

**Bad Example:**
```html
<!-- Inconsistent terminology and placement -->
<!-- Page 1 -->
<button>Save Changes</button>
<button>Discard</button>

<!-- Page 2 -->
<button>Cancel</button>
<button>Submit</button>

<!-- Page 3 -->
<button>Confirm</button>
<button>Back</button>
```

**Common Violations:**
- Different terms for same action ("Delete" vs "Remove" vs "Discard")
- Inconsistent navigation structure
- Primary button sometimes left, sometimes right
- Icons mean different things in different contexts

### 5. Error Prevention

**Principle:** Prevent problems from occurring by careful design.

**What to Check:**
- ✅ Input validation (format, constraints)
- ✅ Confirmation for destructive actions
- ✅ Constraints prevent invalid states
- ✅ Helpful default values
- ✅ Clear labels and instructions
- ✅ Disable invalid options

**Good Example:**
```html
<!-- Prevent invalid input -->
<label for="email">Email Address</label>
<input
  type="email"
  id="email"
  required
  pattern="[^@\s]+@[^@\s]+\.[^@\s]+"
  aria-describedby="email-help"
>
<small id="email-help">We'll never share your email</small>

<!-- Confirmation for destructive action -->
<button onclick="confirmDelete()">Delete Account</button>
<script>
function confirmDelete() {
  if (confirm('Are you sure? This will permanently delete your account and all data.')) {
    deleteAccount();
  }
}
</script>
```

**Bad Example:**
```html
<!-- No validation, no confirmation -->
<input type="text" name="email">
<button onclick="deleteAccount()">Delete</button>
```

**Common Violations:**
- No input validation until form submission
- Delete actions without confirmation
- Unclear which fields are required
- No guidance on password requirements

### 6. Recognition Rather Than Recall

**Principle:** Minimize memory load by making objects, actions, and options
visible.

**What to Check:**
- ✅ Recently used items shown
- ✅ Autocomplete for inputs
- ✅ Visual indicators of state
- ✅ Tooltips for icons
- ✅ Search history
- ✅ Breadcrumbs showing location

**Good Example:**
```html
<!-- Recently used items -->
<div class="recent-searches">
  <h3>Recent Searches</h3>
  <ul>
    <li><a href="?q=usability+testing">usability testing</a></li>
    <li><a href="?q=heuristic+evaluation">heuristic evaluation</a></li>
  </ul>
</div>

<!-- Autocomplete -->
<input
  type="search"
  list="search-suggestions"
  placeholder="Search..."
>
<datalist id="search-suggestions">
  <option value="usability testing">
  <option value="user research">
  <option value="accessibility">
</datalist>
```

**Bad Example:**
```html
<!-- User must remember exact search query -->
<input type="search" placeholder="Search...">
<!-- No history, no suggestions, no help -->
```

**Common Violations:**
- No recently viewed items
- No autocomplete for common inputs
- Icons without labels or tooltips
- Complex commands must be memorized

### 7. Flexibility and Efficiency of Use

**Principle:** Accelerators for expert users while remaining accessible to novices.

**What to Check:**
- ✅ Keyboard shortcuts
- ✅ Bulk actions
- ✅ Customizable workflows
- ✅ Quick actions for common tasks
- ✅ Search as alternative to browse
- ✅ Templates and presets

**Good Example:**
```html
<!-- Keyboard shortcuts with visual hints -->
<button>
  New Document <kbd>Ctrl+N</kbd>
</button>
<button>
  Save <kbd>Ctrl+S</kbd>
</button>

<!-- Bulk actions -->
<div class="bulk-actions">
  <input type="checkbox" id="select-all"> Select All
  <button disabled>Delete Selected (0)</button>
  <button disabled>Export Selected (0)</button>
</div>
```

**Bad Example:**
```html
<!-- No shortcuts, must click through menus for every action -->
<button onclick="navigateToNew()">New Document</button>
<!-- Each document must be deleted individually -->
```

**Common Violations:**
- No keyboard shortcuts for common actions
- No bulk operations
- Can't customize interface
- No quick-create options

### 8. Aesthetic and Minimalist Design

**Principle:** Avoid irrelevant or rarely needed information.

**What to Check:**
- ✅ Only essential information shown
- ✅ Clear visual hierarchy
- ✅ Adequate whitespace
- ✅ Progressive disclosure
- ✅ Focused content (one primary action)
- ✅ Clean, uncluttered interface

**Good Example:**
```html
<!-- Clean, focused interface -->
<div class="search-page">
  <h1>Search</h1>
  <form>
    <input type="search" placeholder="What are you looking for?" autofocus>
    <button type="submit">Search</button>
  </form>
  <a href="/advanced-search">Advanced search</a>
</div>
```

**Bad Example:**
```html
<!-- Cluttered with unnecessary elements -->
<div class="page">
  <div class="banner-ad"></div>
  <div class="promo-popup"></div>
  <div class="newsletter-signup"></div>
  <div class="social-media-feeds"></div>
  <!-- Search form buried somewhere in the noise -->
</div>
```

**Common Violations:**
- Too many options presented at once
- Advertising overshadows content
- Unnecessary decorative elements
- Information overload on primary pages

### 9. Help Users Recognize, Diagnose, and Recover from Errors

**Principle:** Error messages in plain language, precisely indicate the problem,
and constructively suggest a solution.

**What to Check:**
- ✅ Clear error messages (what went wrong)
- ✅ Specific problem identified
- ✅ Suggested solutions provided
- ✅ Errors shown near relevant fields
- ✅ Visual error indicators
- ✅ Help recovering from error state

**Good Example:**
```html
<!-- Clear, helpful error message -->
<div class="form-group error">
  <label for="password">Password</label>
  <input
    type="password"
    id="password"
    aria-invalid="true"
    aria-describedby="password-error"
  >
  <div class="error-message" id="password-error" role="alert">
    <strong>Password too short.</strong>
    Please use at least 8 characters including one number and one special character.
    <a href="/help/passwords">Password requirements</a>
  </div>
</div>
```

**Bad Example:**
```html
<!-- Vague, unhelpful error -->
<div class="error">
  Error: Invalid input (ERR_400)
</div>
<!-- User has no idea what's wrong or how to fix it -->
```

**Common Violations:**
- Generic error messages ("An error occurred")
- Technical error codes without explanation
- No indication which field has error
- No suggestion for fixing the problem

### 10. Help and Documentation

**Principle:** Provide help that is easy to search, focused on user's task,
lists concrete steps, and not too large.

**What to Check:**
- ✅ Context-sensitive help
- ✅ Searchable documentation
- ✅ Step-by-step instructions
- ✅ Video tutorials
- ✅ FAQ section
- ✅ In-app tooltips

**Good Example:**
```html
<!-- Context-sensitive help -->
<div class="feature-card">
  <h3>Data Export</h3>
  <p>Export your data in various formats</p>
  <button class="help-icon" aria-label="Help">
    <span>?</span>
  </button>
  <div class="tooltip">
    <h4>How to export data</h4>
    <ol>
      <li>Select date range</li>
      <li>Choose export format (CSV, JSON, PDF)</li>
      <li>Click Export button</li>
    </ol>
    <a href="/docs/export">Learn more</a>
  </div>
</div>
```

**Bad Example:**
```html
<!-- No help available -->
<div class="complex-feature">
  <h3>Advanced Configuration</h3>
  <!-- Complex interface with no guidance -->
</div>
```

**Common Violations:**
- No help documentation
- Help is hard to find
- Documentation not searchable
- Generic help not task-focused

## Running Evaluations

### Basic Evaluation

```bash
# Evaluate using Nielsen's 10 heuristics
ux-tool heuristics --url https://example.com

# Specify output format
ux-tool heuristics --url https://example.com \
  --output-format html \
  --output evaluation-report.html
```

### Multi-Page Evaluation

```bash
# Evaluate multiple pages
cat > pages.txt << EOF
https://example.com/
https://example.com/products
https://example.com/checkout
https://example.com/dashboard
EOF

ux-tool heuristics --pages-file pages.txt \
  --output multi-page-evaluation.html
```

### Custom Checklist Evaluation

```bash
# Use custom heuristics
ux-tool heuristics --url https://example.com \
  --checklist custom-heuristics.yaml \
  --output custom-evaluation.html
```

### Python API

```python
from ux_research.validator import UsabilityValidator

# Initialize validator
validator = UsabilityValidator()

# Load default checklist (Nielsen's 10)
validator.load_default_checklist()

# Or load custom checklist
validator.load_checklist("custom-heuristics.yaml")

# Run evaluation
results = await validator.evaluate_url("https://example.com")

# Get scores
scores = validator.get_heuristic_scores(results)
for heuristic, score in scores.items():
    print(f"{heuristic}: {score}/10")

# Get violations
violations = validator.get_violations(results)
for violation in violations:
    print(f"Heuristic: {violation.heuristic}")
    print(f"Severity: {violation.severity}")
    print(f"Description: {violation.description}")
    print(f"Recommendation: {violation.recommendation}")
```

## Custom Checklists

### Creating Custom Checklists

```yaml
# custom-heuristics.yaml

metadata:
  name: "E-commerce Usability Heuristics"
  version: "1.0"
  author: "UX Team"
  description: "Custom heuristics for e-commerce platforms"

heuristics:
  # Standard Nielsen heuristic (modified)
  - id: H1
    name: "Visibility of System Status"
    description: "Keep users informed about order and cart status"
    weight: 10
    checks:
      - id: H1.1
        description: "Shopping cart shows item count"
        severity: high
        how_to_check: "Look for cart icon with badge showing number of items"
        pass_criteria: "Cart icon displays item count at all times"

      - id: H1.2
        description: "Order status is clearly displayed"
        severity: high
        how_to_check: "Navigate to order history page"
        pass_criteria: "Each order shows current status (processing, shipped, delivered)"

      - id: H1.3
        description: "Real-time inventory shown"
        severity: medium
        how_to_check: "View product detail pages"
        pass_criteria: "Products show stock availability (in stock, low stock, out of stock)"

  # Custom e-commerce heuristic
  - id: C1
    name: "Checkout Flow Efficiency"
    description: "Streamlined, secure checkout process"
    weight: 10
    checks:
      - id: C1.1
        description: "Guest checkout available"
        severity: high
        how_to_check: "Start checkout without logging in"
        pass_criteria: "Can complete purchase without creating account"

      - id: C1.2
        description: "Saved payment methods"
        severity: medium
        how_to_check: "Return user checkout flow"
        pass_criteria: "Previously used payment methods are saved and selectable"

      - id: C1.3
        description: "Clear shipping costs"
        severity: high
        how_to_check: "Progress through checkout"
        pass_criteria: "Shipping costs displayed before payment information entry"

      - id: C1.4
        description: "Order summary always visible"
        severity: medium
        how_to_check: "Complete checkout flow"
        pass_criteria: "Order total and items visible on all checkout pages"

  # Product discovery heuristic
  - id: C2
    name: "Product Discovery and Search"
    description: "Easy product finding and filtering"
    weight: 9
    checks:
      - id: C2.1
        description: "Search autocomplete"
        severity: high
        how_to_check: "Type in search box"
        pass_criteria: "Suggestions appear after 2-3 characters"

      - id: C2.2
        description: "Faceted filtering"
        severity: high
        how_to_check: "Browse category pages"
        pass_criteria: "Can filter by price, size, color, brand, etc."

      - id: C2.3
        description: "Sort options"
        severity: medium
        how_to_check: "View product listing"
        pass_criteria: "Can sort by relevance, price, rating, newest"

  # Trust and security heuristic
  - id: C3
    name: "Trust and Security"
    description: "Build confidence in transactions"
    weight: 9
    checks:
      - id: C3.1
        description: "Security badges visible"
        severity: high
        how_to_check: "View checkout pages"
        pass_criteria: "SSL badge and payment security icons displayed"

      - id: C3.2
        description: "Return policy clear"
        severity: high
        how_to_check: "Search for return policy"
        pass_criteria: "Return policy linked from footer and product pages"

      - id: C3.3
        description: "Customer reviews shown"
        severity: medium
        how_to_check: "View product pages"
        pass_criteria: "Products show ratings and reviews"

  # Mobile experience heuristic
  - id: C4
    name: "Mobile Commerce Experience"
    description: "Optimized mobile shopping"
    weight: 8
    checks:
      - id: C4.1
        description: "Touch-friendly targets"
        severity: high
        how_to_check: "Test on mobile device"
        pass_criteria: "All interactive elements are at least 44x44 pixels"

      - id: C4.2
        description: "Mobile payment options"
        severity: high
        how_to_check: "Mobile checkout flow"
        pass_criteria: "Apple Pay, Google Pay, or similar available"

      - id: C4.3
        description: "Thumb-zone navigation"
        severity: medium
        how_to_check: "Review mobile navigation"
        pass_criteria: "Key actions accessible in lower third of screen"

# Severity definitions
severity_levels:
  critical:
    score: 1
    description: "Complete blocker, unusable"
  high:
    score: 3
    description: "Major usability problem"
  medium:
    score: 5
    description: "Moderate usability issue"
  low:
    score: 8
    description: "Minor usability concern"
  pass:
    score: 10
    description: "Meets criteria"
```

### Domain-Specific Heuristics

**Healthcare Applications:**
```yaml
heuristics:
  - id: HC1
    name: "Patient Safety"
    checks:
      - "Critical alerts are prominently displayed"
      - "Allergy information always visible"
      - "Medication conflicts flagged"

  - id: HC2
    name: "HIPAA Compliance"
    checks:
      - "PHI is encrypted"
      - "Session timeout after inactivity"
      - "Access logs maintained"
```

**Financial Services:**
```yaml
heuristics:
  - id: FIN1
    name: "Transaction Security"
    checks:
      - "Two-factor authentication required"
      - "Transaction confirmations sent"
      - "Account activity monitoring"

  - id: FIN2
    name: "Regulatory Compliance"
    checks:
      - "Terms and conditions clear"
      - "Fee disclosures prominent"
      - "Privacy policy accessible"
```

## Scoring Methodology

### Severity Ratings

**Critical (Score: 1/10)**
- Complete usability failure
- Users cannot complete task
- Immediate fix required

**High (Score: 3/10)**
- Major usability problem
- Significant friction
- Fix in next sprint

**Medium (Score: 5/10)**
- Moderate usability issue
- Some user confusion
- Fix in next 2-3 sprints

**Low (Score: 7/10)**
- Minor usability concern
- Slight improvement possible
- Fix when convenient

**Pass (Score: 10/10)**
- Fully meets heuristic
- No issues found
- Best practice followed

### Overall Score Calculation

```python
# Per-heuristic score
heuristic_score = sum(check_scores) / num_checks

# Weighted overall score
overall_score = sum(heuristic_score * weight for each heuristic) / sum(weights)

# Example:
# Heuristic 1 (weight 10): 7/10
# Heuristic 2 (weight 9): 5/10
# Heuristic 3 (weight 8): 9/10

overall = (7*10 + 5*9 + 9*8) / (10+9+8)
        = (70 + 45 + 72) / 27
        = 6.9/10 (69%)
```

### Grade Scale

- **9.0-10.0 (A)**: Excellent usability
- **7.0-8.9 (B)**: Good usability, minor improvements
- **5.0-6.9 (C)**: Fair, significant improvements needed
- **3.0-4.9 (D)**: Poor usability
- **0.0-2.9 (F)**: Severe usability problems

## Recommendations

### Prioritization Matrix

```
Impact vs Effort:

High Impact, Low Effort → Quick Wins (Do First)
High Impact, High Effort → Major Projects (Plan Carefully)
Low Impact, Low Effort → Fill-ins (Do When Time Allows)
Low Impact, High Effort → Avoid (Deprioritize)
```

### Example Recommendations

```markdown
# Heuristic Evaluation Recommendations

## Quick Wins (High Impact, Low Effort)

### 1. Add Loading Indicators
**Heuristic:** Visibility of System Status
**Current Score:** 3/10
**Issue:** No feedback during data loads
**Recommendation:** Add spinner/progress bar for operations >1 second
**Effort:** 2 hours
**Impact:** High (improves perceived performance)

### 2. Improve Error Messages
**Heuristic:** Error Recovery
**Current Score:** 4/10
**Issue:** Generic "Error occurred" messages
**Recommendation:** Specific error messages with solutions
**Effort:** 4 hours
**Impact:** High (reduces support tickets)

## Major Projects (High Impact, High Effort)

### 1. Redesign Checkout Flow
**Heuristic:** User Control and Freedom
**Current Score:** 5/10
**Issue:** Cannot go back in checkout, no save for later
**Recommendation:** Multi-step wizard with back/cancel options
**Effort:** 2 weeks
**Impact:** High (increase conversion rate)

## Backlog (Low Priority)

### 1. Add Keyboard Shortcuts
**Heuristic:** Flexibility and Efficiency
**Current Score:** 7/10
**Recommendation:** Implement common shortcuts (Ctrl+S, Ctrl+N)
**Effort:** 1 week
**Impact:** Medium (benefits power users)
```

## Case Studies

### Case Study 1: E-commerce Checkout

**Before:**
- No guest checkout (users must create account)
- Shipping costs not shown until final step
- No order summary visible during checkout
- No save for later option
- Overall Score: 4.2/10

**After:**
- Guest checkout implemented
- Shipping calculator on first step
- Sticky order summary sidebar
- Save for later added
- Overall Score: 8.7/10

**Impact:**
- 23% increase in checkout completion
- 45% reduction in cart abandonment
- 31% decrease in support inquiries

### Case Study 2: SaaS Dashboard

**Before:**
- No loading states for data fetches
- Inconsistent navigation structure
- No keyboard shortcuts
- Help documentation hard to find
- Overall Score: 5.1/10

**After:**
- Loading skeletons for all async operations
- Standardized left sidebar navigation
- Common keyboard shortcuts implemented
- Context-sensitive help tooltips
- Overall Score: 8.9/10

**Impact:**
- 40% reduction in time to complete tasks
- 52% increase in user satisfaction (CSAT)
- 28% decrease in support tickets

## Best Practices

### 1. Multiple Evaluators

```bash
# Conduct evaluation with 3-5 evaluators independently
# Then aggregate findings

# Evaluator 1
ux-tool heuristics --url https://example.com \
  --evaluator "Jane Doe" \
  --output evaluator1.json

# Evaluator 2
ux-tool heuristics --url https://example.com \
  --evaluator "John Smith" \
  --output evaluator2.json

# Aggregate results
ux-tool heuristics aggregate \
  --inputs evaluator1.json,evaluator2.json,evaluator3.json \
  --output aggregated-report.html
```

### 2. Regular Evaluations

```bash
# Schedule quarterly evaluations
# Track scores over time

Q1: 6.2/10
Q2: 7.1/10 (+0.9)
Q3: 7.8/10 (+0.7)
Q4: 8.5/10 (+0.7)
```

### 3. Combine with User Testing

```
1. Heuristic Evaluation (identify potential issues)
2. User Testing (validate with real users)
3. Analytics Review (confirm impact)
4. Iterate
```

### 4. Document Rationale

```markdown
# Decision Log

## Violation: No undo for email deletion

**Heuristic:** User Control and Freedom (H3)
**Severity:** High
**Decision:** Implement "Undo" notification (24-hour retention)
**Rationale:** Analytics show 12% of deletions are accidental
**Implementation:** Sprint 23
**Validation:** A/B test shows 89% use undo when needed
```

## Quick Reference

```bash
# Basic evaluation
ux-tool heuristics --url https://example.com

# Custom checklist
ux-tool heuristics --url https://example.com \
  --checklist custom-heuristics.yaml

# Multi-page evaluation
ux-tool heuristics --pages-file pages.txt

# Export to PDF
ux-tool heuristics --url https://example.com \
  --output-format pdf \
  --output evaluation.pdf
```

## Next Steps

1. **Run your first evaluation**: Use Nielsen's 10 heuristics
2. **Create custom checklist**: Tailor to your domain
3. **Combine with accessibility**: Run both audits together
4. **Validate with users**: Conduct usability testing
5. **Track improvements**: Regular re-evaluation

## Related Guides

- [Accessibility Testing](accessibility_testing.md) - WCAG compliance
- [Feedback Analysis](feedback_analysis.md) - User insights
- [CI/CD Integration](ci_cd_integration.md) - Automated testing
