# User Research Methodology

This document provides comprehensive UX research methods to help designers deeply understand user needs and behaviors.

## Table of Contents
1. [Research Overview](#research-overview)
2. [Qualitative Research Methods](#qualitative-research-methods)
3. [Quantitative Research Methods](#quantitative-research-methods)
4. [User Modeling](#user-modeling)
5. [Usability Testing](#usability-testing)
6. [Research Tools and Templates](#research-tools-and-templates)

---

## Research Overview

### Research Type Comparison

| Type | Purpose | Methods | Output |
|------|---------|---------|--------|
| Exploratory | Discover problems and opportunities | Interviews, field studies | Insights, opportunity areas |
| Descriptive | Understand current state | Surveys, analytics | Data reports |
| Evaluative | Validate designs | Usability testing | Improvement recommendations |
| Causal | Validate hypotheses | A/B testing | Statistical conclusions |

### Research Timing

```
Project Phase          Research Methods
─────────────────────────────────────
Discovery             User interviews
                      Competitive analysis
                      Field studies

Definition            Surveys
                      Card sorting
                      User journey maps

Design                Concept testing
                      Paper prototype testing

Validation            Usability testing
                      A/B testing

Post-launch           Analytics data
                      Satisfaction surveys
                      Continuous optimization
```

---

## Qualitative Research Methods

### User Interviews

**Interview Types:**
| Type | Description | Duration |
|------|-------------|----------|
| Structured | Fixed question order | 30-45 minutes |
| Semi-structured | Has outline but flexible | 45-60 minutes |
| Open-ended | Free conversation | 60-90 minutes |

**Interview Preparation:**
```markdown
1. Define research objectives
2. Write interview guide
3. Recruit participants (5-8 people)
4. Prepare recording equipment
5. Prepare consent forms
```

**Interview Techniques:**
```
✅ Open-ended questions: "Tell me about how you usually...?"
✅ Probe for details: "Can you tell me more about that?"
✅ Explore context: "Under what circumstances does this happen?"
✅ Silent pauses: Give participants time to think

❌ Avoid leading: "You would probably want this feature, right?"
❌ Avoid assumptions: "Everyone does it this way..."
❌ Avoid jargon: "Do you use APIs?"
```

**Interview Guide Template:**
```markdown
## Opening (5 minutes)
- Self-introduction
- Explain interview purpose
- Confirm recording consent

## Background (10 minutes)
- Please briefly introduce yourself
- What is your profession/role?
- How long have you been using [product type]?

## Core Questions (30 minutes)
- Describe your most recent experience with [target behavior]
- What difficulties did you encounter?
- How did you solve these problems?
- What would the ideal experience look like?

## Wrap-up (5 minutes)
- Is there anything else you'd like to add?
- Thank you for participating
```

### Contextual Inquiry

Observe and interview users in their actual usage environment.

**Process:**
```
1. Observe: User performs daily tasks
2. Ask: "Why did you do it that way?"
3. Record: Behaviors, environment, tools, pain points
4. Verify: Confirm understanding is correct
```

**Suitable Scenarios:**
- Understanding workflows
- Discovering hidden needs
- Observing real environmental constraints

### Focus Groups

**Specifications:**
```
Participants: 6-10 people
Duration: 90-120 minutes
Sessions: 2-3 sessions
Moderator: 1 person
Note-taker: 1 person
```

**Suitable Scenarios:**
- Exploring attitudes and preferences
- Collecting diverse perspectives
- Generating new ideas

**Considerations:**
```
⚠️ Groupthink risk
⚠️ Dominant participant influence
⚠️ Social desirability bias
```

### Diary Studies

Users record experiences over a period of time.

**Design:**
```
Duration: 1-4 weeks
Frequency: Daily or event-triggered
Tools: App, forms, voice
Content: Behaviors, emotions, context
```

**Record Template:**
```markdown
## Date: ___________
## Time: ___________

What happened?
_________________________

How were you feeling? (1-5)
😞 😐 😊 😄 🤩

Why did you feel this way?
_________________________

Screenshot or photo (optional)
```

---

## Quantitative Research Methods

### Surveys

**Survey Design Principles:**
```
✅ Questions are clear and concise
✅ Avoid double negatives
✅ Provide appropriate options
✅ Arrange in logical order
✅ Control survey length (5-10 minutes)

❌ Avoid leading questions
❌ Avoid jargon
❌ Avoid sensitive questions at the start
```

**Common Scales:**

**Likert Scale:**
```
Strongly Disagree ─ Disagree ─ Neutral ─ Agree ─ Strongly Agree
       1              2          3        4           5
```

**NPS (Net Promoter Score):**
```
How likely are you to recommend our product to a friend or colleague?

0  1  2  3  4  5  6  7  8  9  10
└────────┴──────────┴─────────┘
Detractors  Passives   Promoters
  (0-6)      (7-8)      (9-10)

NPS = Promoters% - Detractors%
```

**SUS (System Usability Scale):**
```
10-question standardized survey, score 0-100
> 80.3: Excellent
68-80.3: Good
68: Average
< 68: Needs improvement
```

**CSAT (Customer Satisfaction):**
```
How satisfied are you with this experience?
😞 😐 😊 😄 🤩
 1   2   3   4   5

CSAT = (Satisfied responses / Total responses) × 100%
```

### Analytics Data

**Key Metrics:**
| Metric | Description |
|--------|-------------|
| DAU/MAU | Daily/Monthly active users |
| Retention | Retention rate |
| Churn | Churn rate |
| Conversion | Conversion rate |
| Task Success | Task completion rate |
| Time on Task | Task duration |
| Error Rate | Error rate |

**Funnel Analysis:**
```
Homepage visit    100%
    ↓
Product page      60%  (-40%)
    ↓
Add to cart       25%  (-35%)
    ↓
Checkout page     15%  (-10%)
    ↓
Purchase complete 8%   (-7%)
```

### A/B Testing

**Testing Process:**
```
1. Define hypothesis
   "Changing the button from blue to green will increase click rate"

2. Design variants
   A: Blue button (control)
   B: Green button (treatment)

3. Allocate traffic
   50% / 50% random assignment

4. Collect data
   Run long enough to reach statistical significance

5. Analyze results
   Calculate p-value, confirm significance
```

**Sample Size Calculation:**
```
Consider:
- Baseline conversion rate
- Minimum Detectable Effect (MDE)
- Statistical significance (usually 95%)
- Statistical power (usually 80%)
```

---

## User Modeling

### Persona

**Persona Template:**
```markdown
┌─────────────────────────────────────────────────────┐
│ 📷                                                  │
│ [Photo]    Amy Chen, 32                             │
│           Marketing Manager @ Tech Company          │
│           San Francisco, CA                         │
├─────────────────────────────────────────────────────┤
│ Background                                          │
│ 8 years in tech industry, responsible for digital  │
│ marketing strategy. Uses multiple SaaS tools daily │
│ to manage projects and teams.                      │
├─────────────────────────────────────────────────────┤
│ Goals                                  │ Pain Points│
│ • Improve team efficiency              │ • Too many │
│ • Track project progress               │   tools    │
│ • Produce compelling reports           │ • Scattered│
│                                        │   info     │
│                                        │ • Learning │
│                                        │   curve    │
├─────────────────────────────────────────────────────┤
│ "I need a place that integrates all my data,        │
│  so I don't have to switch between different tools."│
├─────────────────────────────────────────────────────┤
│ Tools: Slack, Notion, Google Analytics, Figma       │
│ Tech Proficiency: ████████░░ 80%                    │
└─────────────────────────────────────────────────────┘
```

**Persona Types:**
| Type | Description |
|------|-------------|
| Primary | Main target users |
| Secondary | Secondary users |
| Supplemental | Edge case users |
| Negative | Non-target users |

### User Journey Map

```
Stage       Discover    Research    Purchase    Use         Advocate
─────────────────────────────────────────────────────────────
Touchpoints  Ads         Website     Cart        App         Social
             Search      Reviews     Support     Notifs      Word of mouth
─────────────────────────────────────────────────────────────
Behaviors    See ad      Compare     Add to      Daily       Share
             Click link  features    cart        use         Recommend
                        Read        Fill info   Set
                        reviews                 reminders
─────────────────────────────────────────────────────────────
Thoughts     What is     Is this     Worth it?   How to      This is
             this?       for me?     Safe?       use?        great!
             Looks       Other
             interesting options?               Problems?    Should
                                                            recommend
─────────────────────────────────────────────────────────────
Emotions     😐         🤔          😰          😊          😄
─────────────────────────────────────────────────────────────
Opportunities・Clear     ・Highlight ・Simplify  ・Onboarding・Reward
             value prop  advantages  process     tutorial    program
                        ・Social    ・Security  ・Instant   ・Share
                        proof       guarantee   support     features
```

### Empathy Map

```
┌─────────────────────┬─────────────────────┐
│       Says          │       Thinks        │
│                     │                     │
│ "This process is    │ Why is this so      │
│  too complicated"   │ complicated?        │
│ "Can't find the     │ There must be an    │
│  feature I need"    │ easier way          │
│                     │                     │
├─────────────────────┼─────────────────────┤
│       Does          │       Feels         │
│                     │                     │
│ Repeatedly tries    │ 😤 Frustrated       │
│ different buttons   │ 😰 Anxious          │
│ Asks colleagues     │ 😞 Disappointed     │
│ for help            │                     │
│ Gives up and uses   │                     │
│ another tool        │                     │
│                     │                     │
└─────────────────────┴─────────────────────┘
```

---

## Usability Testing

### Test Planning

**Test Types:**
| Type | Description | Stage |
|------|-------------|-------|
| Formative | Find problems and improve | During design |
| Summative | Evaluate overall performance | Pre-launch |
| Comparative | Compare different versions | During iteration |

**Number of Participants:**

```
5-User Rule (Jakob Nielsen):
- 5 users can find approximately 85% of usability problems
- More users have diminishing returns
- Recommended: Multiple rounds (3-5 people/round)

Large-scale testing:
- Quantitative data needs larger samples
- Recommend 20+ people for statistical significance
```

### Test Script

```markdown
## Introduction (5 minutes)

Hi, thank you for participating in today's test. I'm [name], and today
I'll ask you to try our [product name].

A few notes:
- We're testing the product, not testing you
- There are no right or wrong answers
- Please think aloud
- Difficulties are normal, that's what we want to find
- This will take about 45 minutes
- We need to record, is that okay?

Any questions?

## Warm-up Task (5 minutes)

First, please browse the homepage and tell me what you see.
What do you think this product does?

## Core Tasks (25-30 minutes)

### Task 1: [Task Name]
Scenario: [Describe usage context]
Goal: [Specific thing to accomplish]

"Suppose you want to [scenario], please begin."

Observations:
- [ ] Completed
- [ ] Time: _____ seconds
- [ ] Error count: _____
- [ ] Help requests: _____

### Task 2: [Task Name]
...

## Closing Questions (5-10 minutes)

- Overall, what do you think of this product?
- What did you like most?
- What was most frustrating?
- Any other suggestions?

Thank you for participating!
```

### Test Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| Task Completion Rate | Percentage successfully completing tasks | > 80% |
| Task Time | Time needed to complete tasks | Varies by task |
| Error Rate | Number of errors made | < 2 |
| Help Rate | Percentage needing assistance | < 10% |
| Satisfaction | Subjective satisfaction level | > 4/5 |

### Problem Severity Levels

```
🔴 Critical
   User cannot complete the task
   Fix immediately

🟠 Major
   User can complete but with great difficulty
   Priority fix

🟡 Minor
   Causes inconvenience but can complete
   Scheduled fix

🟢 Cosmetic
   Does not affect usage
   Fix when time permits
```

### Test Report

```markdown
# Usability Test Report

## Summary
- Test dates: 2024/01/15-20
- Participants: 6
- Version tested: v2.1.0

## Key Findings

### 🔴 Critical Issues
1. **Problem Description**
   - Frequency: 6/6 people
   - Impact: Cannot complete registration
   - Recommendation: [Solution]

### 🟠 Major Issues
1. **Problem Description**
   ...

## Metrics Summary

| Task | Completion | Avg Time | Satisfaction |
|------|------------|----------|--------------|
| Registration | 50% | 180s | 2.5/5 |
| Search | 100% | 45s | 4.2/5 |
| Purchase | 83% | 120s | 3.8/5 |

## Recommendations
1. [Priority improvements]
2. [Secondary improvements]
3. [Long-term planning]
```

---

## Research Tools and Templates

### Recommended Research Tools

| Purpose | Tools |
|---------|-------|
| Remote interviews | Zoom, Google Meet, Teams |
| Usability testing | Maze, UserTesting, Lookback |
| Surveys | Typeform, Google Forms, SurveyMonkey |
| Analytics | Google Analytics, Mixpanel, Amplitude |
| Heatmaps | Hotjar, FullStory, Crazy Egg |
| Collaboration notes | Notion, Miro, FigJam |
| Recruitment | UserInterviews, Respondent |

### Research Plan Template

```markdown
# Research Plan

## Project Information
- Project name:
- Researcher:
- Date:

## Research Objectives
1. [Objective 1]
2. [Objective 2]

## Research Questions
1. [Question 1]
2. [Question 2]

## Method
- Method: [Interview/Testing/Survey]
- Participants: [Number and criteria]
- Timeline: [Dates]

## Recruitment Criteria
- Age:
- Experience:
- Exclusions:

## Timeline
| Phase | Date |
|-------|------|
| Preparation | |
| Recruitment | |
| Execution | |
| Analysis | |
| Report | |

## Deliverables
- [ ] Research report
- [ ] Presentation
- [ ] Video clips
```

### Research Ethics

```markdown
## Informed Consent Key Points

□ Research purpose explanation
□ Participation content and duration
□ Recording notification
□ Data usage scope
□ Confidentiality clause
□ Voluntary participation statement
□ Right to withdraw
□ Contact information
□ Signature field
```
