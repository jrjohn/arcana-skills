# Keyword-Triggered Module Prediction

> **Purpose**: During Phase 2 (Step 4) smart prediction, automatically trigger module prediction based on keywords in user requirements text

---

## Core Principles

1. **Scan Original User Requirements**: Not just SDD, also trace back to SRS and original conversation
2. **Keyword Matching**: Use keyword table to trigger module prediction
3. **Bidirectional Validation**: After prediction, verify if SDD already contains it; if not, add it
4. **Priority Ordering**: P0 modules must exist, P1 strongly recommended, P2 optional

---

## Keyword Trigger Table

### ENGAGE Module (Gamification/Retention)

| Trigger Keywords | Predicted Screens | Priority |
|------------------|-------------------|----------|
| retention, engagement, active | All ENGAGE screens | P0 |
| gamification, gamify | SCR-ENGAGE-001-pet, 002-shop, 004-badges | P0 |
| badge, achievement | SCR-ENGAGE-004-badges | P0 |
| reward, points | SCR-ENGAGE-006-daily-reward | P0 |
| pet, character nurturing | SCR-ENGAGE-001-pet, 002-accessories | P1 |
| shop, store, exchange | SCR-ENGAGE-003-shop | P1 |
| leaderboard, ranking | SCR-ENGAGE-005-leaderboard | P1 |
| streak, daily check-in | SCR-ENGAGE-006-daily-reward | P1 |

**ENGAGE Module Complete Screen List**:
```
SCR-ENGAGE-001-pet          Pet/Character
SCR-ENGAGE-002-accessories  Accessories/Decorations
SCR-ENGAGE-003-shop         Shop/Exchange
SCR-ENGAGE-004-badges       Badges/Achievements
SCR-ENGAGE-005-leaderboard  Leaderboard
SCR-ENGAGE-006-daily-reward Daily Rewards
```

---

### SOCIAL Module (Community/Sharing)

| Trigger Keywords | Predicted Screens | Priority |
|------------------|-------------------|----------|
| public, share with others | All SOCIAL screens | P0 |
| share | SCR-SOCIAL-001-share | P0 |
| invite, friend | SCR-SOCIAL-003-invite | P1 |
| community | SCR-SOCIAL-002-public-list | P1 |
| feedback, opinion | SCR-SOCIAL-004-feedback | P2 |
| rating, review | SCR-SOCIAL-004-feedback | P2 |

**SOCIAL Module Complete Screen List**:
```
SCR-SOCIAL-001-share        Share
SCR-SOCIAL-002-public-list  Public Content Browse
SCR-SOCIAL-003-invite       Invite Friends
SCR-SOCIAL-004-feedback     Feedback
```

---

### VOCAB Module Extension (Vocabulary Management)

| Trigger Keywords | Predicted Screens | Priority |
|------------------|-------------------|----------|
| merge | SCR-VOCAB-XXX-merge | P1 |
| group, categorize | SCR-VOCAB-XXX-group | P1 |
| export | SCR-VOCAB-XXX-export | P0 |
| batch | SCR-VOCAB-XXX-batch | P1 |
| publish | SCR-VOCAB-XXX-publish | P1 |
| edit word | SCR-VOCAB-XXX-edit-word | P0 |
| filter, quick filter | SCR-VOCAB-XXX-filter | P1 |

**VOCAB Extension Screen List**:
```
SCR-VOCAB-XXX-edit-word     Edit Word
SCR-VOCAB-XXX-export        Export Vocabulary
SCR-VOCAB-XXX-merge         Merge Vocabulary
SCR-VOCAB-XXX-group         Group Management
SCR-VOCAB-XXX-filter        Quick Filter
SCR-VOCAB-XXX-batch         Batch Operations
SCR-VOCAB-XXX-publish       Publish Public
SCR-VOCAB-XXX-ocr-result    OCR Result Confirmation
```

---

### PROGRESS Module Extension (Progress/Reports)

| Trigger Keywords | Predicted Screens | Priority |
|------------------|-------------------|----------|
| report, statistics | All PROGRESS extensions | P0 |
| weekly report | SCR-PROGRESS-XXX-weekly | P1 |
| calendar | SCR-PROGRESS-XXX-calendar | P1 |
| trend | SCR-PROGRESS-XXX-trend | P2 |
| skill, ability | SCR-PROGRESS-XXX-skills | P1 |
| ranking | SCR-PROGRESS-XXX-ranking | P2 |

**PROGRESS Extension Screen List**:
```
SCR-PROGRESS-XXX-weekly     Weekly Report
SCR-PROGRESS-XXX-calendar   Learning Calendar
SCR-PROGRESS-XXX-skills     Skills Analysis
SCR-PROGRESS-XXX-trend      Trend Charts
SCR-PROGRESS-XXX-ranking    Ranking Statistics
SCR-PROGRESS-XXX-daily      Daily Details
```

---

### TRAIN Module Extension (Training Modes)

| Trigger Keywords | Predicted Screens | Priority |
|------------------|-------------------|----------|
| adventure, stage | SCR-TRAIN-XXX-adventure-map, level-start | P1 |
| mixed, comprehensive | SCR-TRAIN-XXX-mixed | P1 |
| level, stage | SCR-TRAIN-XXX-level-start | P1 |
| challenge | SCR-TRAIN-XXX-challenge | P2 |
| timed, timer | (UI element, not standalone screen) | - |

**TRAIN Extension Screen List**:
```
SCR-TRAIN-XXX-mixed         Mixed Mode
SCR-TRAIN-XXX-adventure-map Adventure Map
SCR-TRAIN-XXX-level-start   Level Start
SCR-TRAIN-XXX-challenge     Challenge Mode
```

---

### SETTING Module Extension (Settings Pages)

| Trigger Keywords | Predicted Screens | Priority |
|------------------|-------------------|----------|
| terms, terms of service | SCR-SETTING-XXX-terms | P1 |
| privacy policy | SCR-SETTING-XXX-privacy-policy | P1 |
| licenses, open source | SCR-SETTING-XXX-licenses | P2 |
| changelog, update log | SCR-SETTING-XXX-changelog | P2 |
| help, FAQ | SCR-SETTING-XXX-help | P1 |
| learning settings | SCR-SETTING-XXX-learning | P1 |
| reminder, notification | SCR-SETTING-XXX-reminder | P1 |
| sync | SCR-SETTING-XXX-sync | P1 |
| theme, appearance | SCR-SETTING-XXX-theme | P1 |

**SETTING Extension Screen List**:
```
SCR-SETTING-XXX-terms           Terms of Service
SCR-SETTING-XXX-privacy-policy  Privacy Policy
SCR-SETTING-XXX-licenses        Open Source Licenses
SCR-SETTING-XXX-changelog       Changelog
SCR-SETTING-XXX-help            Help Center
SCR-SETTING-XXX-learning        Learning Settings
SCR-SETTING-XXX-reminder        Reminder Settings
SCR-SETTING-XXX-sync            Sync Settings
SCR-SETTING-XXX-theme           Theme Settings
```

---

### HOME/DASH Module (Home Screen)

| Trigger Keywords | Predicted Screens | Priority |
|------------------|-------------------|----------|
| parent, guardian | SCR-HOME-002-parent or separate PARENT module | P0 |
| student, child | SCR-HOME-001-student or DASH | P0 |
| multi-role, role | HOME-001 + HOME-002 separation | P0 |

---

## Smart Prediction Execution Flow

```
Step 4: Execute Smart Prediction
│
├── 4.1 Scan Original Requirements Text
│   ├── Read user original conversation
│   ├── Read SRS functional requirements
│   └── Extract keyword list
│
├── 4.2 Keyword Matching
│   ├── Match against this document's trigger table
│   ├── Record triggered modules and screens
│   └── Sort by priority
│
├── 4.3 Compare with Existing SDD
│   ├── Check Appendix A screen list
│   ├── Mark existing screens
│   └── List missing screens
│
├── 4.4 Generate Prediction Report
│   ├── Must add (P0)
│   ├── Strongly recommended (P1)
│   └── Optional (P2)
│
└── 4.5 Update screen-prediction.json
    └── Output to 04-ui-flow/workspace/
```

---

## Prediction Report Format

```json
{
  "prediction_date": "2026-01-16",
  "source_keywords": [
    "maximize user retention",
    "users can choose to make vocabulary public",
    "vocabulary can be optionally merged, grouped, or exported"
  ],
  "triggered_modules": {
    "ENGAGE": {
      "trigger": "retention",
      "priority": "P0",
      "screens": ["pet", "shop", "badges", "leaderboard", "daily-reward"],
      "status": "missing"
    },
    "SOCIAL": {
      "trigger": "public vocabulary",
      "priority": "P0",
      "screens": ["share", "public-list", "invite"],
      "status": "missing"
    },
    "VOCAB_EXTEND": {
      "trigger": "merge, group, export",
      "priority": "P1",
      "screens": ["merge", "group", "export"],
      "status": "partial"
    }
  },
  "analysis": {
    "existing_screens": 49,
    "predicted_missing": 25,
    "total_recommended": 74
  },
  "action_required": [
    "Add ENGAGE module (6 screens)",
    "Add SOCIAL module (4 screens)",
    "Extend VOCAB module (+5 screens)",
    "Extend SETTING module (+6 screens)",
    "Extend PROGRESS module (+2 screens)",
    "Extend TRAIN module (+2 screens)"
  ]
}
```

---

## Validation Script

```bash
#!/bin/bash
# keyword-prediction-check.sh
# Check keywords in SRS/user requirements and predict missing modules

SRS_FILE="$1"
SDD_FILE="$2"

echo "🔍 Keyword-triggered prediction check..."

# ENGAGE keywords
ENGAGE_KEYWORDS="retention|engagement|active|gamification|badge|reward|pet|shop|leaderboard"
if grep -qiE "$ENGAGE_KEYWORDS" "$SRS_FILE"; then
  echo "⚠️ ENGAGE keywords detected"
  if ! grep -q "SCR-ENGAGE" "$SDD_FILE"; then
    echo "  ❌ SDD missing ENGAGE module! Recommend adding 6 screens"
  fi
fi

# SOCIAL keywords
SOCIAL_KEYWORDS="public|share|community|invite|friend"
if grep -qiE "$SOCIAL_KEYWORDS" "$SRS_FILE"; then
  echo "⚠️ SOCIAL keywords detected"
  if ! grep -q "SCR-SOCIAL" "$SDD_FILE"; then
    echo "  ❌ SDD missing SOCIAL module! Recommend adding 4 screens"
  fi
fi

# VOCAB extension keywords
VOCAB_EXT="merge|group|export|batch"
if grep -qiE "$VOCAB_EXT" "$SRS_FILE"; then
  echo "⚠️ VOCAB extension keywords detected"
  VOCAB_COUNT=$(grep -c "SCR-VOCAB" "$SDD_FILE")
  if [ "$VOCAB_COUNT" -lt 12 ]; then
    echo "  ⚠️ VOCAB module may be incomplete (current $VOCAB_COUNT, recommend 12+)"
  fi
fi

echo ""
echo "Keyword prediction check complete"
```

---

## Integration with common-modules

Keyword-triggered prediction should execute after common-modules validation:

```
Phase 2 Smart Prediction Order:
1. common-modules required module validation (AUTH, PROFILE, SETTING, COMMON)
2. App type requirements loading (education-requirements.md, etc.)
3. Keyword-triggered prediction (this document) ← New
4. Button Navigation navigation gap analysis
5. Naming convention inference (detail pages, edit pages, etc.)
```

---

## Important Notes

1. **No Duplicate Prediction**: If module already exists in SDD, don't add again
2. **Maintain ID Continuity**: Use next available number when adding new screens
3. **Update Appendix A**: After prediction, must update SDD screen list
4. **User Confirmation**: P1/P2 priority predictions should be confirmed with user
