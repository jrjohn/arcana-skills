# Medical Software Requirements Interview Question Bank

## Directory
1. [Project Vision Questions](#1-project-vision-questions)
2. [User Analysis Questions](#2-user-analysis-questions)
3. [Functional Requirements Questions](#3-functional-requirements-questions)
4. [Technical Constraints Questions](#4-technical-constraints-questions)
5. [Business Rules Questions](#5-business-rules-questions)
6. [Integration Requirements Questions](#6-integration-requirements-questions)
7. [Medical-Specific Questions](#7-medical-specific-questions)

---

## 1. Project Vision Questions

### Problem Solving
- What problem does this project solve?
- How do users currently handle this problem? What are the pain points?
- Why are existing solutions not good enough?
- If we don't do this project, what will be the consequences?

### Business Goals
- What are the business goals of this project?
- How do we measure project success? What are the KPIs?
- What is the expected ROI?
- How does this project align with the company's overall strategy?

### Scope Boundary Definition
- What are the core functions of the project? (Must Have)
- Which functions are Nice to Have?
- Which functions are explicitly out of scope?
- What is the scope of the first version (MVP)?

---

## 2. User Analysis Questions

### User Identification
- Who are the main users? Please describe their characteristics
- Are there secondary users or stakeholders?
- What are the differences in requirements between different user groups?
- What is the technical proficiency level of users?

### Usage Context
- In what situations do users typically use this system?
- What is the typical user workflow?
- On which devices will users use this?
- What is the usage frequency? (daily/weekly/monthly)

### User Journey
- What will users do when they first encounter the system?
- What are the steps to complete the main tasks?
- Which steps are most prone to errors or confusion?
- How do users learn to complete tasks?

---

## 3. Functional Requirements Questions

### Core Functions
- What core functions must the system provide?
- What are the inputs and outputs of each function?
- What are the dependencies between functions?
- Which functions need special attention to performance?

### Data Requirements
- What data does the system need to process?
- What is the data source?
- What is the data format and structure?
- How is the data lifecycle managed?
- What are the data quality requirements?

### Search and Reports
- What data do users need to search?
- What filter and sort functions are needed?
- What reports need to be generated?
- What are the report formats and export requirements?

### Notifications and Reminders
- What notifications does the system need to send?
- What are the notification triggers?
- What notification methods are available? (Email/Push/SMS)
- How can users manage notification preferences?

---

## 4. Technical Constraints Questions

### Existing Systems
- Which existing systems need to be integrated?
- What technology does the existing system use?
- What data needs to be migrated from the old system?
- Do new and old systems need to run in parallel?

### Technical Environment
- Are there designated technical platforms or frameworks?
- What is the deployment environment? (cloud/on-premise/hybrid)
- Are there any infrastructure limitations?
- What technologies is the team familiar with?

### Performance Constraints
- What is the expected number of users?
- What is the expected data volume?
- What are the performance requirements? (response time/throughput)
- What is the peak load situation?

---

## 5. Business Rules Questions

### Permissions and Roles
- What user roles does the system have?
- What operations can each role perform?
- How are permissions granted and revoked?
- What data access restrictions exist?

### Workflow
- What workflows require approval?
- What are the approval levels and conditions?
- How to handle exception situations?
- What automatic transition rules exist?

### Validation Rules
- What validation rules exist for data input?
- What are the business logic validation conditions?
- How to handle validation failures?
- What data consistency requirements exist?

### Calculation Rules
- What fields need to be calculated?
- What are the calculation formulas?
- What are the calculation timing and triggers?
- How to round calculation results?

---

## 6. Integration Requirements Questions

### External Systems
- Which external systems need to be integrated?
- What is the integration method? (API/File/Database)
- What is the data synchronization frequency?
- How to handle integration failures?

### Third-party Services
- What third-party services need to be used?
- What is the service SLA?
- Is there a backup plan?
- What is the fee structure?

### Data Exchange
- What is the data exchange format?
- What is the data exchange protocol?
- What security requirements exist?
- How to handle data conversion?

---

## Interview Skills Reminders

### Open-Ended Questions
- Use "what", "how", "what is" as openers
- Avoid leading questions
- Give interviewee time to think

### Follow-up Techniques
- "Can you give an example?"
- "Are there other situations?"
- "What if...?"
- "Why is this important?"

### Confirming Understanding
- "Let me confirm my understanding..."
- "So what you mean is..."
- "Is this correct...?"

### Recording Points
- Requirement source (who provided it)
- Requirement priority level
- Requirement rationale
- Items to be confirmed

---

## 7. Medical-Specific Questions

### Clinical Workflow
- In what clinical scenarios will this software be used?
- What is the current clinical workflow?
- Which steps are most prone to errors or delays?
- How will the software integrate into the existing clinical workflow?
- Does it need to integrate with existing medical standard operating procedures (SOP)?

### Patient Safety
- What impact could software failure have on patients?
- In the worst case scenario, what harm could occur?
- What safety-critical functions need special protection?
- What alerts or blocking mechanisms are needed?
- How to ensure patient identity is not confused?

### Software Safety Classification
- Will the software directly affect diagnosis or treatment decisions?
- When software fails, do clinical staff have sufficient time to take remedial measures?
- Does the software control or monitor life-sustaining devices?
- What is the expected software safety classification: Class A, B, or C?

### Regulatory Requirements
- Does the software need to apply for TFDA/FDA/CE approval?
- What regulations or standards must be followed? (IEC 62304, ISO 14971, etc.)
- Is third-party validation or certification needed?
- What documents need to be submitted to regulatory authorities?

### Data Privacy
- What personal health information (PHI) will the software process?
- Where will data be stored? (on-premise/cloud)
- Are there cross-border data transfer requirements?
- How long does data need to be retained?
- What de-identification requirements exist?

### Medical System Integration
- Which medical systems need to be integrated? (HIS/LIS/RIS/PACS)
- What medical data exchange standards are used? (HL7/FHIR/DICOM)
- Do existing systems support these standards?
- What are the real-time requirements for data synchronization?

### Usage Environment
- In what environment will the software be used? (operating room/ward/outpatient/home)
- Will users potentially be wearing gloves during operation?
- Does it need to be quickly accessible in emergency situations?
- Are there special environmental constraints? (infection control/electromagnetic interference)

### Medical Device Connection
- Does it need to connect to medical devices?
- What is the device communication protocol?
- How is device data transmitted and stored?
- How to handle device disconnection?

### Medication Safety
- Is the software involved in medication prescription or administration?
- What medication safety checks are needed? (allergies/drug interactions/dosage)
- Does it need to connect to a medication database?
- What is the priority level and handling method for medication alerts?

### Audit Tracking
- What operations need to record audit trails?
- What information needs to be included in audit logs?
- How long do audit logs need to be retained?
- Who has permission to access audit logs?
