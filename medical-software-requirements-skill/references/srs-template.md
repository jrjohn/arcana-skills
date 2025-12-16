# SRS Software Requirements Specification Template
## Software Requirements Specification Template

Aligned with IEC 62304 Standard

---

## Directory

1. [Document Information](#1-document-Information)
2. [Product Overview](#2-product-overview)
3. [Functional Requirements](#3-functional-Requirements)
4. [Non-Functional Requirements](#4-non-functional-Requirements)
5. [Interface Requirements](#5-Interface-Requirements)
6. [Software Safety Classification](#6-software-safety-classification)
7. [Appendix](#7-appendix)

---

## 1. Document Information

| Items | Content |
|-----|------|
| Document Number | SRS-[projectCode]-[Version] |
| Document Name | [Product Name] Software Requirements Specification |
| Version | [X.X] |
| Creation Date | [YYYY-MM-DD] |
| Last Modified Date | [YYYY-MM-DD] |
| Author | [Name] |
| Reviewer | [Name] |
| Approver | [Name] |

### 1.1 Version History

| Version | Date | Changes | Author |
|-----|------|---------|------|
| 1.0 | [YYYY-MM-DD] | Initial Version Created | [Name] |

### 1.2 Reference Documents

| Document Number | Document Name | Version |
|---------|---------|------|
| [Number] | [Name] | [Version] |

---

## 2. Product Overview

### 2.1 Product Purpose

[Describe the product's main purpose and intended use]

### 2.2 Product Scope

[Describe the product's functional scope and boundaries]

### 2.3 User Characteristics

| User Type | Description | Technical Skill Level |
|-----------|------|---------|
| [Type1] | [Description] | [High/Medium/Low] |

### 2.4 Intended Use Environment

[Describe the software's intended operating environment]

### 2.5 Assumptions and Limitations

**Assumptions**:
- [Assumption 1]

**Limitations**:
- [Limitation 1]

---

## 3. Functional Requirements

### 3.1 Requirements Overview

| ID | Requirement Name | Priority Level | Safety Classification |
|----|---------|--------|---------|
| SRS-001 | [Requirement Name] | [High/Medium/Low] | [A/B/C] |
| SRS-002 | [Requirement Name] | [High/Medium/Low] | [A/B/C] |

### 3.2 Requirement Detailed Description

---

#### SRS-001 [Requirement Name]

| Property | Content |
|-----|------|
| **ID** | SRS-001 |
| **Name** | [Requirement Name] |
| **Description** | [The system shall...] |
| **Source** | [Source document or stakeholder] |
| **Priority Level** | [High/Medium/Low] |
| **Safety Classification** | [Class A/B/C] |
| **Verification Method** | [Test/Analysis/Inspection/Demonstration] |
| **Preconditions** | [Preconditions] |
| **Postconditions** | [Postconditions] |
| **Related Requirements** | [Related SRS-xxx ID] |

**Acceptance Criteria**:
1. [Criterion 1]
2. [Criterion 2]

**Notess**:
[Additional supplementary description]

---

#### SRS-002 [Requirement Name]

| Property | Content |
|-----|------|
| **ID** | SRS-002 |
| **Name** | [Requirement Name] |
| **Description** | [The system shall...] |
| **Source** | [Source document or stakeholder] |
| **Priority Level** | [High/Medium/Low] |
| **Safety Classification** | [Class A/B/C] |
| **Verification Method** | [Test/Analysis/Inspection/Demonstration] |
| **Preconditions** | [Preconditions] |
| **Postconditions** | [Postconditions] |
| **Related Requirements** | [Related SRS-xxx ID] |

**Acceptance Criteria**:
1. [Criterion 1]

---

## 4. Non-Functional Requirements

### 4.1 Performance Requirements

#### SRS-NFR-001 [Performance Requirement Name]

| Property | Content |
|-----|------|
| **ID** | SRS-NFR-001 |
| **Type** | Performance |
| **Description** | [The system shall complete... within X seconds] |
| **Measurement Criteria** | [Measurable performance criteria] |
| **Verification Method** | [Test/Analysis] |

### 4.2 Security Requirements

#### SRS-NFR-002 [Security Requirement Name]

| Property | Content |
|-----|------|
| **ID** | SRS-NFR-002 |
| **Type** | Security |
| **Description** | [Describe Security requirement] |
| **Verification Method** | [Test/Analysis/Inspection] |

### 4.3 Reliability Requirements

#### SRS-NFR-003 [Reliability Requirement Name]

| Property | Content |
|-----|------|
| **ID** | SRS-NFR-003 |
| **Type** | Reliability |
| **Description** | [Describe reliability requirement] |
| **MTBF** | [Mean time between failures] |
| **Verification Method** | [Test/Analysis] |

### 4.4 Maintainability Requirements

#### SRS-NFR-004 [Maintainability Requirement Name]

| Property | Content |
|-----|------|
| **ID** | SRS-NFR-004 |
| **Type** | Maintainability |
| **Description** | [Describe maintainability requirement] |
| **Verification Method** | [Inspection/Analysis] |

---

## 5. Interface Requirements

### 5.1 User Interface Requirements

#### SRS-UI-001 [UI Requirement Name]

| Property | Content |
|-----|------|
| **ID** | SRS-UI-001 |
| **Description** | [Describe UI requirement] |
| **Related Screen** | [Screen Name/Number] |

### 5.2 Hardware Interface Requirements

#### SRS-HW-001 [Hardware Interface Requirement Name]

| Property | Content |
|-----|------|
| **ID** | SRS-HW-001 |
| **Description** | [Describe hardware Interface requirement] |
| **Communication Protocol** | [Protocol name] |

### 5.3 Software Interface Requirements

#### SRS-SW-001 [Software Interface Requirement Name]

| Property | Content |
|-----|------|
| **ID** | SRS-SW-001 |
| **Description** | [Describe software Interface requirement] |
| **API Specification** | [API description] |

### 5.4 Communication Interface Requirements

#### SRS-COM-001 [Communication Interface Requirement Name]

| Property | Content |
|-----|------|
| **ID** | SRS-COM-001 |
| **Description** | [Describe communication Interface requirement] |
| **Protocol** | [Protocol name] |
| **Bandwidth Requirements** | [Requirement description] |

---

## 6. Software Safety Classification

### 6.1 Classification Basis

According to IEC 62304 Standard, software safety classification is based on the potential harm level caused by software failure:

| Classification | Definition | Applicable to This System |
|-----|------|-----------|
| Class A | No injury or damage to health possible | [Yes/No] |
| Class B | Non-serious injury possible | [Yes/No] |
| Class C | Death or serious injury possible | [Yes/No] |

### 6.2 This System Classification

**Overall Software Safety Classification**: [Class A/B/C]

**Classification Rationale**:
[Describe why this classification was selected]

### 6.3 Function-Specific Safety Classification

| Function ID | Function Name | Safety Classification | Classification Rationale |
|--------|---------|---------|---------|
| SRS-001 | [Name] | [A/B/C] | [Rationale] |

---

## 7. Appendix

### 7.1 Technical Terms Definition

| Technical Term | Definition |
|-----|------|
| [Term 1] | [Definition] |

### 7.2 Abbreviations

| Abbreviation | Full Name |
|-----|------|
| SRS | Software Requirements Specification |
| IEC | International Electrotechnical Commission |

---

## Approval

| Role | Name | Signature | Date |
|-----|------|------|------|
| Author | | | |
| Reviewer | | | |
| Approver | | | |
