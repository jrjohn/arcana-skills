# Requirements Interview Question Bank

This document provides question templates for **Step 0: Requirements Interview**.

---

## ⚠️ Step 0 Quick Interview (Mandatory First Step)

> **Important**: Before writing any documents (SRS/SDD), the requirements interview must be completed first.
> Use the `AskUserQuestion` tool for interactive interview.

### Quick Interview Question Template (Using AskUserQuestion)

The following questions should use the AskUserQuestion tool, asking 2-4 questions at a time with options for user selection.

---

#### Round 1: Basic Architecture & Experience Design

**Q1: Target Platform**
```json
{
  "question": "What is the primary target platform for the App? (This affects technical architecture and UI design)",
  "header": "Platform",
  "options": [
    {"label": "iPhone + iPad (Recommended)", "description": "Support both devices for maximum coverage"},
    {"label": "iPad Only", "description": "Focus on large screen learning experience"},
    {"label": "iPhone + iPad + Mac (Catalyst)", "description": "Full Apple ecosystem support"}
  ]
}
```

**Q2: Account Architecture**
```json
{
  "question": "How should user account relationships be designed?",
  "header": "Accounts",
  "options": [
    {"label": "Family Group (1 Parent + Multiple Students)", "description": "Parent manages multiple child accounts, suitable for multi-child families"},
    {"label": "Independent Accounts + Linking", "description": "Students have independent accounts, parents link via invitation code to supervise"},
    {"label": "Single Account Role Switching", "description": "Switch between parent/student modes within the same account"}
  ]
}
```

**Q3: Visual Style**
```json
{
  "question": "What visual style preference for the App?",
  "header": "Style",
  "options": [
    {"label": "Playful & Fun (Recommended)", "description": "Bright colors, rounded corners, cute illustrations, suitable for children"},
    {"label": "Clean & Modern", "description": "Clean interface, neutral colors, suitable for focused learning"},
    {"label": "Gamified Interface", "description": "Rich animations, badges, rewards, leaderboards"}
  ]
}
```

**Q4: Primary Color Selection**
```json
{
  "question": "What primary color preference for the App? (This affects brand identity and overall visuals)",
  "header": "Color",
  "options": [
    {"label": "Vibrant Orange-Yellow (Recommended)", "description": "Warm, lively, stimulates learning motivation, suitable for children's education"},
    {"label": "Fresh Blue-Green", "description": "Cool, focused, easy on eyes, suitable for long study sessions"},
    {"label": "Soft Pink-Purple", "description": "Warm, friendly, reduces stress"},
    {"label": "Natural Green", "description": "Calm, healthy, eco-friendly image"}
  ]
}
```

**Q5: Dark Mode Support**
```json
{
  "question": "Should dark mode be supported?",
  "header": "Dark Mode",
  "options": [
    {"label": "Supported (Recommended)", "description": "Follows system settings automatically, protects eyes"},
    {"label": "Light Mode Only", "description": "Simplifies development, common approach for children's apps"},
    {"label": "User Selectable", "description": "Manual toggle between light/dark mode in settings"}
  ]
}
```

**Q6: Offline Functionality**
```json
{
  "question": "What level of offline functionality support?",
  "header": "Offline",
  "options": [
    {"label": "Full Offline (Recommended)", "description": "Vocabulary/progress cached locally, complete offline learning"},
    {"label": "Partial Offline", "description": "Downloaded content available offline, new content requires network"},
    {"label": "Network Required", "description": "All features require internet connection"}
  ]
}
```

---

#### Round 2: Technical Stack Selection

**Q7: AI Service Selection** (If AI features needed)
```json
{
  "question": "What AI service preference for sentence generation?",
  "header": "AI Service",
  "options": [
    {"label": "Claude API (Recommended)", "description": "Anthropic's Claude, excellent performance in Traditional Chinese"},
    {"label": "OpenAI API", "description": "GPT series, high market maturity"},
    {"label": "Either (Configurable)", "description": "Provides flexibility but increases maintenance complexity"}
  ]
}
```

**Q8: Voice Technology Selection** (If voice features needed)
```json
{
  "question": "What voice technology selection?",
  "header": "Voice",
  "options": [
    {"label": "iOS Native (AVSpeechSynthesizer)", "description": "Free, offline available, but lower voice naturalness"},
    {"label": "Cloud Service (Amazon Polly / Azure)", "description": "High-quality natural voices, but requires payment and network"},
    {"label": "Hybrid Mode (Recommended)", "description": "Default native, optional premium cloud voices"}
  ]
}
```

---

#### Round 3: Feature Priority & Data Sync

**Q9: MVP Core Features**
```json
{
  "question": "What core features are essential for first version (MVP)?",
  "header": "MVP Features",
  "options": [
    {"label": "Listening + Spelling Tests", "description": "Basic learning features"},
    {"label": "Listening + Spelling + Pronunciation Tests", "description": "Complete language learning"},
    {"label": "All Features (Listening/Pronunciation/Spelling/Matching/Fill-in)", "description": "Full version"}
  ],
  "multiSelect": true
}
```

**Q10: Data Sync Requirements**
```json
{
  "question": "Is cross-device data sync needed?",
  "header": "Data Sync",
  "options": [
    {"label": "iCloud Sync (Recommended)", "description": "Apple native solution, seamless user experience"},
    {"label": "Custom Backend Sync", "description": "Full control, but requires server maintenance"},
    {"label": "Local Storage Only", "description": "Simple implementation, but no cross-device support"}
  ]
}
```

---

### Interview Results Recording Template

After interview completion, organize results in the following format as basis for SRS writing:

```markdown
## Interview Results Summary

**Interview Date:** YYYY-MM-DD
**Project Name:** {Project Name}

### Basic Architecture
- **Target Platform:** iPhone + iPad
- **Account Architecture:** Family Group (1 Parent + Multiple Students)
- **Data Sync:** iCloud Sync

### Technical Stack
- **AI Service:** Claude API
- **Voice Technology:** Hybrid Mode (Native + Optional Cloud)
- **Offline Support:** Full Offline

### Feature Priority
- **MVP Features:** Listening + Spelling + Pronunciation Tests
- **Phase 2:** Matching + Fill-in
- **Deferred Features:** Gamification Leaderboard

### Visual & Experience
- **Visual Style:** Playful & Fun
- **Primary Color:** Vibrant Orange-Yellow (Primary: #FF9500, Secondary: #FFCC00)
- **Dark Mode:** Supported (follows system settings)
- **Target Age:** Elementary middle grades (8-10 years old)

### Special Requirements
- {User-specific requirements}
```

---

## Detailed Interview Question Bank

Below are more detailed interview questions, selectable based on project complexity.

---

## Table of Contents
1. [Project Vision Questions](#1-project-vision-questions)
2. [User Analysis Questions](#2-user-analysis-questions)
3. [Functional Requirements Questions](#3-functional-requirements-questions)
4. [Technical Constraints Questions](#4-technical-constraints-questions)
5. [Business Rules Questions](#5-business-rules-questions)
6. [Integration Requirements Questions](#6-integration-requirements-questions)
7. [Healthcare-Specific Questions](#7-healthcare-specific-questions)

---

## 1. Project Vision Questions

### Problem Solving
- What problem does this project solve?
- How do users currently handle this problem? What are their pain points?
- Why are existing solutions insufficient?
- What are the consequences of not doing this project?

### Business Goals
- What are the business goals for this project?
- How do we measure project success? What are the KPIs?
- What is the expected ROI?
- How does this project align with overall company strategy?

### Scope Definition
- What are the core features? (Must Have)
- Which features are Nice to Have?
- What features are explicitly out of scope?
- What is the first version (MVP) scope?

---

## 2. User Analysis Questions

### User Identification
- Who are the primary users? Please describe their characteristics
- Are there secondary users or stakeholders?
- How do different user groups' needs differ?
- What is users' technical proficiency level?

### Usage Scenarios
- In what scenarios do users typically use this system?
- What is users' typical workflow?
- On which devices will users access the system?
- What is the usage frequency? (Daily/Weekly/Monthly)

### User Journey
- What do users do when they first encounter the system?
- What are the steps for users to complete main tasks?
- Which steps are most prone to errors or confusion?
- How do users know when a task is complete?

---

## 3. Functional Requirements Questions

### Core Features
- What core features must the system provide?
- What are the inputs and outputs for each feature?
- What dependencies exist between features?
- Which features require special attention to performance?

### Data Requirements
- What data does the system need to process?
- What are the data sources?
- What are the data formats and structures?
- How is data lifecycle managed?
- What data quality requirements exist?

### Search & Reporting
- What data do users need to search?
- What filtering and sorting features are needed?
- What reports need to be generated?
- What are the report format and export requirements?

### Notifications & Alerts
- What notifications does the system need to send?
- What are the notification trigger conditions?
- What notification channels exist? (Email/Push/SMS)
- How can users manage notification preferences?

---

## 4. Technical Constraints Questions

### Existing Systems
- What existing systems need integration?
- What technologies do existing systems use?
- What data needs to be migrated from legacy systems?
- Do new and old systems need to run in parallel?

### Technical Environment
- Are there specified technology platforms or frameworks?
- What is the deployment environment? (Cloud/On-premise/Hybrid)
- What infrastructure constraints exist?
- What technologies is the team familiar with?

### Performance Constraints
- What is the expected number of users?
- What is the expected data volume?
- What performance requirements exist? (Response time/Throughput)
- What are peak load scenarios?

---

## 5. Business Rules Questions

### Permissions & Roles
- What user roles exist in the system?
- What operations can each role perform?
- How are permissions granted and revoked?
- What data access restrictions exist?

### Workflows
- What processes require approval?
- What are the approval levels and conditions?
- How are exceptions handled?
- What automation rules exist?

### Validation Rules
- What validation rules exist for data input?
- What are the business logic validation conditions?
- How are validation failures handled?
- What data consistency requirements exist?

### Calculation Rules
- What fields require calculation?
- What are the calculation formulas?
- What are the calculation timing and trigger conditions?
- How are calculation results rounded?

---

## 6. Integration Requirements Questions

### External Systems
- What external systems require integration?
- What is the integration method? (API/File/Database)
- What is the data sync frequency?
- How are integration failures handled?

### Third-Party Services
- What third-party services are needed?
- What is the service SLA?
- Are there backup plans?
- What is the cost structure?

### Data Exchange
- What is the data exchange format?
- What is the data exchange protocol?
- What security requirements exist?
- How is data transformation handled?

---

## Interview Tips

### Open-Ended Questions
- Start with "What," "How," "Why"
- Avoid leading questions
- Give interviewees time to think

### Follow-up Techniques
- "Can you give an example?"
- "Are there other scenarios?"
- "What if...?"
- "Why is this important?"

### Confirm Understanding
- "Let me confirm my understanding..."
- "So you mean..."
- "Is this correct...?"

### Key Points to Record
- Requirement source (who raised it)
- Requirement priority
- Requirement rationale
- Questions pending confirmation

---

## 7. Healthcare-Specific Questions

### Clinical Workflows
- In what clinical scenarios will this software be used?
- What is the current clinical workflow?
- Which steps are most error-prone or cause delays?
- How will the software integrate into existing clinical workflows?
- Does it need to integrate with existing medical SOPs?

### Patient Safety
- What impact could software failure have on patients?
- In worst case scenarios, what harm could occur?
- What safety-critical functions need special protection?
- What warnings or blocking mechanisms are needed?
- How do we ensure patient identity is not confused?

### Software Safety Classification
- Does the software directly affect diagnostic or treatment decisions?
- When software fails, do clinical staff have sufficient time for remedial action?
- Does the software control or monitor life-sustaining equipment?
- What is the expected software safety class: Class A, B, or C?

### Regulatory Requirements
- Does the software need TFDA/FDA/CE approval?
- What regulations or standards must be followed? (IEC 62304, ISO 14971, etc.)
- Is third-party verification or certification needed?
- What documents need to be submitted to regulatory bodies?

### Data Privacy
- What Personal Health Information (PHI) will the software process?
- Where will data be stored? (On-premise/Cloud)
- Are there cross-border data transfer requirements?
- How long must data be retained?
- What de-identification requirements exist?

### Healthcare System Integration
- What healthcare systems need integration? (HIS/LIS/RIS/PACS)
- What medical data exchange standards are used? (HL7/FHIR/DICOM)
- Do existing systems support these standards?
- What are the real-time data sync requirements?

### Usage Environment
- In what environment will the software be used? (OR/Ward/Clinic/Home)
- Will users possibly operate with gloves?
- Is rapid access needed in emergency situations?
- Are there special environmental constraints? (Infection control/EMI)

### Medical Device Connectivity
- Does the software need to connect to medical devices?
- What is the device communication protocol?
- How is device data transmitted and stored?
- How are device disconnections handled?

### Medication Safety
- Does the software involve medication prescribing or administration?
- What medication safety checks are needed? (Allergy/Interactions/Dosage)
- Does it need to connect to medication databases?
- What are medication alert priorities and handling methods?

### Audit Trail
- What operations need audit trail logging?
- What information should audit logs contain?
- How long must audit logs be retained?
- Who has permission to view audit logs?
