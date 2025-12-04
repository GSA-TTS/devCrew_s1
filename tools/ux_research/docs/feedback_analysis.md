# Feedback Analysis Guide

Comprehensive guide to collecting, analyzing, and extracting insights from user
feedback across multiple sources.

## Table of Contents

- [Overview](#overview)
- [Collecting Feedback](#collecting-feedback)
- [Data Formats](#data-formats)
- [Sentiment Analysis](#sentiment-analysis)
- [Theme Extraction](#theme-extraction)
- [NPS Calculation](#nps-calculation)
- [Insights Generation](#insights-generation)
- [Integration Examples](#integration-examples)
- [Best Practices](#best-practices)

## Overview

The UX Research Platform aggregates and analyzes user feedback from multiple
sources to provide actionable insights:

**Supported Sources:**
- Survey responses (CSV, JSON, Excel)
- Support tickets (Zendesk, Freshdesk, JIRA)
- User interviews (text transcripts)
- App store reviews (iOS, Android)
- Social media mentions (Twitter, Reddit)
- Heatmap tools (Hotjar, Crazy Egg)
- Session recordings
- In-app feedback widgets
- Email feedback

**Analysis Types:**
- Sentiment classification (positive/negative/neutral)
- Topic modeling and theme extraction
- Net Promoter Score (NPS) calculation
- Pain point identification
- Feature request prioritization
- User journey insights
- Sentiment trends over time

## Collecting Feedback

### Survey Data

```bash
# Analyze survey responses from CSV
ux-tool feedback --source surveys.csv --analyze sentiment

# Multiple survey files
ux-tool feedback \
  --sources q1-survey.csv,q2-survey.csv,q3-survey.csv \
  --analyze sentiment,themes,nps
```

**Example CSV Format:**
```csv
timestamp,user_id,question,response,nps_score,email
2024-01-15 10:30,user123,"What do you like most?","Easy to use",9,user@example.com
2024-01-15 11:45,user456,"What needs improvement?","Slow loading times",6,user2@example.com
2024-01-15 14:20,user789,"Overall feedback","Great product!",10,user3@example.com
```

### Support Tickets

```bash
# Import from Zendesk
ux-tool feedback \
  --source zendesk \
  --zendesk-domain yourcompany.zendesk.com \
  --zendesk-api-key YOUR_API_KEY \
  --date-range 2024-01-01:2024-01-31

# Import from JIRA
ux-tool feedback \
  --source jira \
  --jira-server https://jira.company.com \
  --jira-project SUPPORT \
  --jql "project=SUPPORT AND type='Bug' AND created >= -30d"
```

### User Interviews

```bash
# Analyze interview transcripts
ux-tool feedback \
  --sources interviews/user1.txt,interviews/user2.txt \
  --analyze themes,sentiment \
  --extract-quotes

# Directory of transcripts
ux-tool feedback \
  --source-dir interviews/ \
  --file-pattern "*.txt" \
  --analyze themes
```

**Example Interview Transcript:**
```text
Interviewer: What challenges do you face with the checkout process?
User: The biggest issue is that I can't save my payment information.
I have to re-enter it every time, which is frustrating.

Interviewer: How would you rate the overall experience?
User: It's pretty good, maybe 7 out of 10. The main product works well,
but these little annoyances add up.
```

### App Store Reviews

```bash
# Scrape iOS App Store reviews
ux-tool feedback \
  --source app-store \
  --app-id 123456789 \
  --country us \
  --analyze sentiment,themes

# Android Play Store reviews
ux-tool feedback \
  --source play-store \
  --package-name com.yourapp \
  --analyze sentiment
```

### Social Media

```bash
# Twitter mentions
ux-tool feedback \
  --source twitter \
  --twitter-query "@yourcompany OR #yourproduct" \
  --days 30 \
  --analyze sentiment

# Reddit posts
ux-tool feedback \
  --source reddit \
  --subreddit yourproduct \
  --analyze sentiment,themes
```

### Hotjar Integration

```bash
# Import Hotjar feedback polls
ux-tool feedback \
  --source hotjar \
  --hotjar-site-id YOUR_SITE_ID \
  --hotjar-api-key YOUR_API_KEY \
  --date-range 2024-01-01:2024-01-31

# Include heatmap insights
ux-tool feedback \
  --source hotjar \
  --include-heatmaps \
  --analyze-heatmaps
```

## Data Formats

### CSV Format

**Required columns:**
- `feedback` or `response` or `comment` (feedback text)

**Optional columns:**
- `timestamp` or `date` (when feedback was given)
- `user_id` or `email` (user identifier)
- `source` (where feedback came from)
- `nps_score` or `rating` (numeric score 0-10)
- `category` or `topic` (pre-categorized)
- `sentiment` (if pre-analyzed)

**Example:**
```csv
timestamp,user_id,source,feedback,nps_score
2024-01-15,user123,survey,"Love the new dashboard!",9
2024-01-16,user456,support,"App crashes on login",3
2024-01-17,user789,interview,"Feature request: dark mode",8
```

### JSON Format

```json
[
  {
    "id": "fb-001",
    "timestamp": "2024-01-15T10:30:00Z",
    "user": {
      "id": "user123",
      "email": "user@example.com",
      "segment": "enterprise"
    },
    "source": "survey",
    "feedback": "The new dashboard is much easier to navigate",
    "nps_score": 9,
    "metadata": {
      "survey_id": "q1-2024",
      "question": "What do you think of the new dashboard?"
    }
  },
  {
    "id": "fb-002",
    "timestamp": "2024-01-16T14:20:00Z",
    "user": {
      "id": "user456",
      "email": "user2@example.com"
    },
    "source": "support_ticket",
    "feedback": "App crashes when I try to export large datasets",
    "priority": "high",
    "ticket_id": "SUPPORT-1234"
  }
]
```

### Text Files

```text
# One feedback item per line, or separated by blank lines

User feedback: The app is great but needs dark mode support.

Another comment: I love the new search feature! It's so much faster
than before. Would be even better with filters.

Suggestion: Please add keyboard shortcuts for common actions.
```

## Sentiment Analysis

### Basic Sentiment Analysis

```bash
# Analyze sentiment in feedback
ux-tool feedback --source feedback.csv --analyze sentiment

# Output sentiment distribution
ux-tool feedback \
  --source feedback.csv \
  --analyze sentiment \
  --output sentiment-report.html
```

**Output Example:**
```
Sentiment Distribution:
- Positive: 456 (62%)
- Neutral: 178 (24%)
- Negative: 103 (14%)

Average Sentiment Score: 0.72 (scale: -1 to 1)

Top Positive Themes:
1. "easy to use" (87 mentions)
2. "great design" (64 mentions)
3. "helpful support" (52 mentions)

Top Negative Themes:
1. "slow performance" (31 mentions)
2. "missing features" (28 mentions)
3. "confusing interface" (19 mentions)
```

### Sentiment by Source

```bash
# Compare sentiment across sources
ux-tool feedback \
  --sources surveys.csv,tickets.json,reviews.csv \
  --analyze sentiment \
  --group-by source \
  --output sentiment-by-source.html
```

**Chart Output:**
```
Source         | Positive | Neutral | Negative | Avg Score
---------------|----------|---------|----------|----------
Surveys        | 75%      | 18%     | 7%       | 0.82
Support        | 22%      | 35%     | 43%      | -0.15
App Reviews    | 68%      | 20%     | 12%      | 0.71
Social Media   | 45%      | 30%     | 25%      | 0.28
```

### Sentiment Trends

```bash
# Track sentiment over time
ux-tool feedback \
  --source feedback.csv \
  --analyze sentiment \
  --trend weekly \
  --output sentiment-trend.html
```

### Python API

```python
from ux_research.analyzer import SentimentAnalyzer

# Initialize analyzer
analyzer = SentimentAnalyzer()

# Analyze single feedback
feedback = "The new update made the app much faster!"
result = analyzer.analyze_sentiment(feedback)

print(f"Sentiment: {result['label']}")  # "positive"
print(f"Score: {result['score']:.2f}")   # 0.94
print(f"Confidence: {result['confidence']:.2f}")  # 0.98

# Batch analysis
feedback_items = [
    "Love the new features!",
    "App keeps crashing",
    "It's okay, nothing special"
]

results = analyzer.analyze_batch(feedback_items)
for item, result in zip(feedback_items, results):
    print(f"{item}: {result['label']} ({result['score']:.2f})")

# Output:
# Love the new features!: positive (0.96)
# App keeps crashing: negative (-0.88)
# It's okay, nothing special: neutral (0.02)
```

## Theme Extraction

### Automatic Theme Discovery

```bash
# Extract main themes from feedback
ux-tool feedback \
  --source feedback.csv \
  --analyze themes \
  --num-themes 10 \
  --output themes-report.html
```

**Output Example:**
```
Top 10 Themes:

1. Performance & Speed (142 mentions)
   - "slow loading"
   - "app performance"
   - "faster response time"
   - "lag when scrolling"

2. User Interface (98 mentions)
   - "intuitive design"
   - "confusing navigation"
   - "clean layout"
   - "hard to find features"

3. Feature Requests (87 mentions)
   - "dark mode"
   - "export to PDF"
   - "bulk actions"
   - "keyboard shortcuts"

4. Mobile Experience (76 mentions)
   - "responsive design"
   - "mobile app needed"
   - "touch gestures"
   - "screen size issues"

5. Customer Support (65 mentions)
   - "helpful support team"
   - "slow response time"
   - "documentation lacking"
   - "tutorial videos"
```

### Theme Sentiment Analysis

```bash
# Analyze sentiment per theme
ux-tool feedback \
  --source feedback.csv \
  --analyze themes,sentiment \
  --combine-analysis \
  --output theme-sentiment.html
```

**Output:**
```
Theme                | Mentions | Positive | Negative | Net Sentiment
---------------------|----------|----------|----------|---------------
Performance & Speed  | 142      | 23%      | 77%      | -54%
User Interface       | 98       | 68%      | 32%      | +36%
Customer Support     | 65       | 82%      | 18%      | +64%
Feature Requests     | 87       | 90%      | 10%      | +80%
Mobile Experience    | 76       | 45%      | 55%      | -10%
```

### Custom Theme Categories

```yaml
# custom-themes.yaml
themes:
  performance:
    keywords:
      - slow
      - fast
      - loading
      - lag
      - speed
      - performance
      - responsive
    synonyms:
      - quick
      - sluggish
      - snappy

  usability:
    keywords:
      - easy
      - difficult
      - intuitive
      - confusing
      - user-friendly
      - complicated
    sentiment_weight: 1.5  # Prioritize usability feedback

  features:
    keywords:
      - feature
      - functionality
      - capability
      - missing
      - wish
      - request
    extract_specific: true
```

```bash
# Use custom theme categories
ux-tool feedback \
  --source feedback.csv \
  --analyze themes \
  --theme-config custom-themes.yaml
```

### Python API

```python
from ux_research.analyzer import ThemeExtractor

extractor = ThemeExtractor()

# Extract themes automatically
feedback_list = [
    "App is too slow to load",
    "Love the new design!",
    "Need dark mode support",
    "Performance has improved"
]

themes = extractor.extract_themes(feedback_list, num_themes=3)

for theme in themes:
    print(f"Theme: {theme['name']}")
    print(f"Keywords: {', '.join(theme['keywords'])}")
    print(f"Mentions: {theme['count']}")
    print(f"Example: {theme['examples'][0]}")
    print()

# Custom theme matching
custom_themes = extractor.load_themes("custom-themes.yaml")
categorized = extractor.categorize_feedback(feedback_list, custom_themes)

for category, items in categorized.items():
    print(f"{category}: {len(items)} items")
```

## NPS Calculation

### Net Promoter Score

NPS measures customer loyalty on a scale of -100 to +100.

**Formula:**
```
NPS = % Promoters - % Detractors

Where:
- Promoters: Score 9-10
- Passives: Score 7-8
- Detractors: Score 0-6
```

### Calculate NPS

```bash
# Calculate NPS from survey data
ux-tool feedback \
  --source nps-survey.csv \
  --analyze nps \
  --output nps-report.html
```

**Output Example:**
```
Net Promoter Score (NPS): +42

Distribution:
- Promoters (9-10): 456 responses (58%)
- Passives (7-8):   213 responses (27%)
- Detractors (0-6): 119 responses (15%)

Total Responses: 788

Industry Benchmarks:
- Your NPS: +42
- SaaS Average: +31
- Industry Leader: +72

Trend: ↑ +7 points vs. last quarter
```

### NPS by Segment

```bash
# Segment NPS analysis
ux-tool feedback \
  --source nps-survey.csv \
  --analyze nps \
  --segment-by customer_type \
  --output nps-by-segment.html
```

**Output:**
```
Segment      | NPS  | Promoters | Passives | Detractors | Sample Size
-------------|------|-----------|----------|------------|-------------
Enterprise   | +68  | 72%       | 24%      | 4%         | 234
SMB          | +35  | 52%       | 31%      | 17%        | 389
Free Tier    | +12  | 41%       | 30%      | 29%        | 165
```

### NPS Trends

```bash
# Track NPS over time
ux-tool feedback \
  --source nps-monthly.csv \
  --analyze nps \
  --trend monthly \
  --output nps-trend.html
```

### Python API

```python
from ux_research.analyzer import NPSCalculator

calculator = NPSCalculator()

# Calculate NPS from scores
nps_scores = [9, 10, 8, 7, 10, 3, 9, 10, 6, 8, 9, 10, 7]
result = calculator.calculate_nps(nps_scores)

print(f"NPS: {result['nps']}")  # +42
print(f"Promoters: {result['promoters_pct']}%")
print(f"Passives: {result['passives_pct']}%")
print(f"Detractors: {result['detractors_pct']}%")

# NPS with feedback
data = [
    {"score": 9, "feedback": "Great product!"},
    {"score": 3, "feedback": "Too expensive"},
    {"score": 10, "feedback": "Excellent support"}
]

analysis = calculator.analyze_nps_feedback(data)

print("Promoter Themes:")
for theme in analysis['promoter_themes']:
    print(f"  - {theme}")

print("Detractor Themes:")
for theme in analysis['detractor_themes']:
    print(f"  - {theme}")
```

## Insights Generation

### Pain Point Identification

```bash
# Identify top user pain points
ux-tool feedback \
  --source feedback.csv \
  --analyze pain-points \
  --severity-threshold high \
  --output pain-points.html
```

**Output Example:**
```
Top 10 User Pain Points:

1. Slow Performance (Severity: High)
   - 87 mentions (12% of feedback)
   - Sentiment: -0.76
   - Most affected: Mobile users
   - Key issues:
     * Page load times >5s
     * Laggy scrolling
     * Timeout errors

2. Confusing Navigation (Severity: Medium)
   - 64 mentions (9% of feedback)
   - Sentiment: -0.52
   - Most affected: New users
   - Key issues:
     * Can't find settings
     * Menu structure unclear
     * No search function
```

### Feature Request Prioritization

```bash
# Prioritize feature requests
ux-tool feedback \
  --source feedback.csv \
  --analyze feature-requests \
  --prioritize-by frequency,impact \
  --output feature-requests.html
```

**Output:**
```
Prioritized Feature Requests:

Rank | Feature          | Mentions | Impact | Effort | Priority Score
-----|------------------|----------|--------|--------|---------------
1    | Dark Mode        | 142      | High   | Low    | 9.2
2    | PDF Export       | 98       | Medium | Low    | 7.8
3    | Bulk Actions     | 87       | High   | Medium | 7.5
4    | Mobile App       | 76       | High   | High   | 6.9
5    | Keyboard Shortcut| 65       | Medium | Low    | 6.4
```

### User Journey Insights

```bash
# Analyze feedback by user journey stage
ux-tool feedback \
  --source feedback.csv \
  --analyze journey \
  --stages onboarding,usage,support \
  --output journey-insights.html
```

### Actionable Recommendations

```bash
# Generate action items from feedback
ux-tool feedback \
  --source feedback.csv \
  --analyze recommendations \
  --include-quotes \
  --output recommendations.html
```

**Output Example:**
```markdown
# Action Items (Next Sprint)

## High Priority

### 1. Improve Page Load Performance
**Evidence:** 87 mentions, -0.76 sentiment
**User Quotes:**
- "Page takes forever to load, very frustrating"
- "I often give up waiting for the dashboard"

**Recommended Actions:**
- Optimize database queries (reduce from 15 to 5)
- Implement lazy loading for images
- Add CDN for static assets
- Target: <2s page load time

**Estimated Impact:** +15 NPS points
**Effort:** 2 weeks

---

### 2. Add Dark Mode
**Evidence:** 142 requests, +0.88 sentiment
**User Quotes:**
- "Dark mode would make this perfect!"
- "My eyes hurt after using this at night"

**Recommended Actions:**
- Implement CSS dark mode theme
- Add toggle in user settings
- Remember user preference
- Test for WCAG contrast compliance

**Estimated Impact:** +8 NPS points
**Effort:** 1 week
```

## Integration Examples

### Zendesk Integration

```python
from ux_research.collector import ZendeskCollector

collector = ZendeskCollector(
    domain="yourcompany.zendesk.com",
    api_key="YOUR_API_KEY"
)

# Fetch recent tickets
tickets = collector.fetch_tickets(
    start_date="2024-01-01",
    end_date="2024-01-31",
    status=["open", "pending", "solved"],
    priority=["urgent", "high"]
)

# Extract feedback
feedback = collector.extract_feedback(tickets)

# Analyze
from ux_research.analyzer import SentimentAnalyzer
analyzer = SentimentAnalyzer()
results = analyzer.analyze_batch(feedback)
```

### Google Forms Integration

```python
from ux_research.collector import GoogleFormsCollector

collector = GoogleFormsCollector(
    credentials_file="service-account.json"
)

# Fetch form responses
responses = collector.fetch_responses(
    form_id="1a2b3c4d5e6f",
    start_date="2024-01-01"
)

# Convert to standard format
feedback = collector.to_feedback_format(responses)
```

### Slack Integration

```python
from ux_research.collector import SlackCollector

collector = SlackCollector(
    token="xoxb-your-token"
)

# Monitor feedback channel
feedback = collector.fetch_channel_messages(
    channel="customer-feedback",
    days=30
)

# Real-time monitoring
collector.monitor_channel(
    channel="customer-feedback",
    callback=analyze_and_alert,
    keywords=["bug", "issue", "problem", "slow"]
)
```

## Best Practices

### 1. Collect Continuously

```bash
# Schedule regular feedback collection
# Cron: Daily at 2 AM
0 2 * * * ux-tool feedback \
  --source zendesk,surveys,app-reviews \
  --analyze sentiment,themes \
  --output /reports/feedback-$(date +\%Y\%m\%d).html
```

### 2. Segment Analysis

```bash
# Analyze by user segment
ux-tool feedback \
  --source feedback.csv \
  --segment-by user_type,plan,region \
  --analyze sentiment,themes
```

### 3. Close the Loop

```python
# Auto-respond to detractors
from ux_research.collector import FeedbackCollector

collector = FeedbackCollector()
feedback = collector.load_from_csv("nps-survey.csv")

detractors = [f for f in feedback if f.nps_score <= 6]

for detractor in detractors:
    # Send personalized follow-up
    send_email(
        to=detractor.email,
        subject="We'd love to hear more",
        template="detractor-followup",
        context={"feedback": detractor.feedback}
    )
```

### 4. Track Trends

```bash
# Compare periods
ux-tool feedback \
  --source q1-feedback.csv \
  --compare-with q4-feedback.csv \
  --analyze trends
```

### 5. Validate with Quantitative Data

```bash
# Combine feedback with analytics
ux-tool report \
  --feedback feedback.json \
  --analytics analytics.json \
  --correlate \
  --output insights-report.html
```

## Next Steps

1. **Set up data collection**: Configure feedback sources
2. **Establish baseline**: Run initial analysis for comparison
3. **Create dashboards**: Visualize feedback trends
4. **Integrate with roadmap**: Prioritize features based on feedback
5. **Continuous monitoring**: Schedule regular analysis

## Quick Reference

```bash
# Basic sentiment analysis
ux-tool feedback --source feedback.csv --analyze sentiment

# Theme extraction
ux-tool feedback --source feedback.csv --analyze themes --num-themes 10

# NPS calculation
ux-tool feedback --source nps-survey.csv --analyze nps

# Multi-source analysis
ux-tool feedback \
  --sources surveys.csv,tickets.json,reviews.csv \
  --analyze sentiment,themes,nps \
  --output comprehensive-report.html

# Pain points identification
ux-tool feedback --source feedback.csv --analyze pain-points

# Feature requests
ux-tool feedback --source feedback.csv --analyze feature-requests
```
