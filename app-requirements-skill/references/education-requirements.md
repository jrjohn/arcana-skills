# Education/Learning App Additional Requirements (REQ-EDU-*)

This document defines additional requirements modules for Education/Learning Apps, used in conjunction with `standard-app-requirements.md`.
Applicable to: Language learning, Vocabulary learning, Quiz practice, Course learning, Skill training, and similar App types.

---

## Trigger Keywords

When user descriptions contain the following keywords, automatically load this requirements module:

- Learning, Education, Teaching, Course
- Vocabulary, Words, Word bank, Question bank
- Quiz, Practice, Test, Exam
- Pronunciation, Listening, Spelling, Phonics
- Parent, Teacher, Student, Child

---

## Content Management Module (REQ-EDU-CONTENT-*)

| ID | Requirement | Description | Priority |
|----|-------------|-------------|----------|
| REQ-EDU-CONTENT-001 | Vocabulary/Question Bank Creation | Users can create, edit, and delete vocabulary or question banks | P0 |
| REQ-EDU-CONTENT-002 | Single Entry Addition | Support single entry addition with required field validation | P0 |
| REQ-EDU-CONTENT-003 | Batch Import | Support batch import in MD/Excel/CSV formats | P0 |
| REQ-EDU-CONTENT-004 | Photo OCR Addition | Add content via camera or gallery with OCR text recognition | P1 |
| REQ-EDU-CONTENT-005 | Selection/Highlight Addition | Select or highlight text in photos for automatic extraction and addition | P1 |
| REQ-EDU-CONTENT-006 | Content Export | Support export to MD/Excel/CSV formats | P1 |
| REQ-EDU-CONTENT-007 | Vocabulary Merge | Merge multiple vocabularies into one | P1 |
| REQ-EDU-CONTENT-008 | Vocabulary Grouping | Group by bookmarks, error frequency, or custom conditions | P1 |
| REQ-EDU-CONTENT-009 | Public Vocabulary Sharing | Users can choose to make vocabulary public for others to load | P2 |
| REQ-EDU-CONTENT-010 | Independent Vocabulary Loading | When loading others' vocabulary, user attributes are independent, not affecting original author | P1 |

---

## Sentence Management Module (REQ-EDU-SENTENCE-*)

| ID | Requirement | Description | Priority |
|----|-------------|-------------|----------|
| REQ-EDU-SENTENCE-001 | Manual Sentence Input | Parents/Teachers can manually input example sentences | P0 |
| REQ-EDU-SENTENCE-002 | AI Auto-Generate Sentences | System automatically generates life-relevant and memorable sentences | P1 |
| REQ-EDU-SENTENCE-003 | AI Timeout Handling | Set AI generation response time (e.g., 5 seconds), use default sentence or prompt retry on timeout | P0 |
| REQ-EDU-SENTENCE-004 | AI Failure Fallback | Provide offline backup sentences when network is abnormal to ensure fluency | P1 |
| REQ-EDU-SENTENCE-005 | Sentence Update Options | After sentence generation, option to keep or regenerate | P1 |
| REQ-EDU-SENTENCE-006 | Bilingual Display | Sentences display bilingual (e.g., English-Chinese) translation | P0 |
| REQ-EDU-SENTENCE-007 | Sentence Pronunciation | Sentences support audio playback | P0 |
| REQ-EDU-SENTENCE-008 | Pronunciation Speed Adjustment | Sentence pronunciation speed adjustable (slow/normal/fast) | P1 |

---

## Learning Features Module (REQ-EDU-LEARN-*)

| ID | Requirement | Description | Priority |
|----|-------------|-------------|----------|
| REQ-EDU-LEARN-001 | Listening Test | Play audio, user selects or inputs corresponding content | P0 |
| REQ-EDU-LEARN-002 | Listening Voice Type | Use natural American accent voice (TTS) | P0 |
| REQ-EDU-LEARN-003 | Listening Speed Adjustment | Speed adjustable (0.5x ~ 2.0x) | P1 |
| REQ-EDU-LEARN-004 | Pronunciation Test | User reads aloud, system performs speech recognition comparison | P0 |
| REQ-EDU-LEARN-005 | Pronunciation Tolerance | Pronunciation comparison allows some degree of error | P1 |
| REQ-EDU-LEARN-006 | Pronunciation Deviation Display | Correct and deviated parts shown in different colors (e.g., green/red) | P1 |
| REQ-EDU-LEARN-007 | Spelling Test | User spells words based on prompts | P0 |
| REQ-EDU-LEARN-008 | Sentence Fill-in-Blank | Fill in correct words in sentences | P1 |
| REQ-EDU-LEARN-009 | Matching Test | Match words with definitions/images | P1 |
| REQ-EDU-LEARN-010 | Test Mode Switching | Freely switch between test modes | P1 |

---

## Progress Tracking Module (REQ-EDU-PROGRESS-*)

| ID | Requirement | Description | Priority |
|----|-------------|-------------|----------|
| REQ-EDU-PROGRESS-001 | Bookmark Marking | Users can bookmark content | P0 |
| REQ-EDU-PROGRESS-002 | Error Frequency Tracking | System records error count and frequency for each item | P0 |
| REQ-EDU-PROGRESS-003 | Learning Statistics | Display study time, completion count, accuracy rate, etc. | P1 |
| REQ-EDU-PROGRESS-004 | Progress Reports | Provide visual progress reports (charts) | P1 |
| REQ-EDU-PROGRESS-005 | Cross-Platform Sync | Learning progress syncs across iOS/iPad/MacOS | P1 |
| REQ-EDU-PROGRESS-006 | Offline Learning | Support offline mode, sync progress when connected | P2 |

---

## Parent/Teacher Participation Module (REQ-EDU-PARENT-*)

| ID | Requirement | Description | Priority |
|----|-------------|-------------|----------|
| REQ-EDU-PARENT-001 | Multi-Role Login | Support student, parent, teacher role login | P0 |
| REQ-EDU-PARENT-002 | Role Permission Differentiation | Different roles have different operation permissions | P0 |
| REQ-EDU-PARENT-003 | Parent Dashboard | Parents can view child's learning progress and statistics | P1 |
| REQ-EDU-PARENT-004 | Vocabulary Assignment | Parents/Teachers can assign vocabulary to students | P1 |
| REQ-EDU-PARENT-005 | Learning Progress Reports | Parents can receive periodic learning reports | P2 |
| REQ-EDU-PARENT-006 | Learning Reminder Settings | Parents can set learning reminder times | P2 |

---

## User Engagement Module (REQ-EDU-ENGAGE-*)

| ID | Requirement | Description | Priority |
|----|-------------|-------------|----------|
| REQ-EDU-ENGAGE-001 | Learning Reward Mechanism | Earn rewards (badges/points) for completing learning tasks | P1 |
| REQ-EDU-ENGAGE-002 | Streak Tracking | Track and display consecutive learning days | P1 |
| REQ-EDU-ENGAGE-003 | Daily Goals | Set daily learning goals and track completion | P1 |
| REQ-EDU-ENGAGE-004 | Learning Reminder Notifications | Push notifications to remind users to learn | P1 |
| REQ-EDU-ENGAGE-005 | Achievement System | Unlock achievements upon reaching specific milestones | P2 |

---

## UX Complexity Control (REQ-EDU-UX-*)

| ID | Requirement | Description | Priority |
|----|-------------|-------------|----------|
| REQ-EDU-UX-001 | Simplified Interface | Optimize interface complexity for target age group | P0 |
| REQ-EDU-UX-002 | Large Button Design | Large touch targets suitable for elementary students | P0 |
| REQ-EDU-UX-003 | Clear Visual Feedback | Operations have clear visual/audio feedback | P1 |
| REQ-EDU-UX-004 | Unified Settings Entry | All settings centralized in one settings button | P1 |
| REQ-EDU-UX-005 | Operation Guidance | Provide operation guidance on first use | P1 |

---

## Requirements Count Estimate

| Module | P0 | P1 | P2 | Subtotal |
|--------|----|----|----|----|
| Content Management | 3 | 6 | 1 | 10 |
| Sentence Management | 4 | 4 | 0 | 8 |
| Learning Features | 4 | 6 | 0 | 10 |
| Progress Tracking | 2 | 3 | 1 | 6 |
| Parent/Teacher | 2 | 2 | 2 | 6 |
| User Engagement | 0 | 4 | 1 | 5 |
| UX Complexity | 2 | 3 | 0 | 5 |
| **Total** | **17** | **28** | **5** | **50** |

Plus generic requirements from `standard-app-requirements.md` (approximately 40-60),
Education/Learning App total requirements estimate: **90-110 requirements**

---

## Integration with Other Modules

This requirements module needs to integrate with the following modules:

| Module | Source | Description |
|--------|--------|-------------|
| Authentication (AUTH) | standard-app-requirements.md | Multi-role login integration |
| Settings (SETTING) | standard-app-requirements.md | Unified settings entry |
| Notification (NOTIFY) | standard-app-requirements.md | Learning reminder notifications |
| Sync (SYNC) | standard-app-requirements.md | Cross-platform progress sync |

---

## Screen List Estimate (SCR-EDU-*)

| Screen Type | Estimated Count | Description |
|-------------|-----------------|-------------|
| Vocabulary Management | 5-8 | List, Add, Edit, Import, Export, etc. |
| Learning Modes | 5-8 | Listening, Pronunciation, Spelling, Fill-in, Matching |
| Progress Statistics | 3-5 | Statistics overview, Report details, Achievements, etc. |
| Parent Features | 3-5 | Dashboard, Assignment, Reports, etc. |
| **Total** | **16-26** | |

---

## Technical Considerations

### Speech Recognition (Pronunciation Test)
- iOS: Speech Framework
- Third-party: Azure Speech / Google Speech-to-Text

### Text-to-Speech (Listening Test)
- iOS: AVSpeechSynthesizer (American accent)
- Third-party: Amazon Polly / Google TTS

### OCR Recognition (Photo Addition)
- iOS: Vision Framework
- Third-party: Google ML Kit / Azure Computer Vision

### AI Sentence Generation
- OpenAI API / Claude API
- Timeout handling: 5 second timeout + local cached sentences
