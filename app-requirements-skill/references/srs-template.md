# SRS-{{PROJECT_CODE}}-1.0

## Software Requirements Specification

**Document ID:** SRS-{{PROJECT_CODE}}-1.0
**Version:** 1.0
**Created Date:** {{DATE}}
**Last Updated:** {{DATE}}
**Project Name:** {{PROJECT_NAME}}
**Document Status:** Draft

---

### Document Approval

| Role | Name | Date |
|------|------|------|
| Author | | |
| Reviewer | | |
| Approver | | |

---

## Table of Contents

1. [Revision History](#1-revision-history)
2. [Product Overview](#2-product-overview)
3. [Functional Requirements](#3-functional-requirements)
4. [Non-Functional Requirements](#4-non-functional-requirements)
5. [Interface Requirements](#5-interface-requirements)
6. [Software Safety Classification](#6-software-safety-classification)
7. [Appendix](#7-appendix)

---

## 1. Revision History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | {{DATE}} | Initial version | |

### 1.1 Reference Documents

| Document ID | Document Name | Version |
|-------------|---------------|---------|
| SDD-{{PROJECT_CODE}}-1.0 | Software Design Description | 1.0 |

---

## 2. Product Overview

### 2.1 Product Purpose

[Describe the main purpose and intended use of the product]

### 2.2 Product Scope

[Describe the functional scope and boundaries of the product]

### 2.3 User Characteristics

| User Type | Description | Technical Level |
|-----------|-------------|-----------------|
| [Type 1] | [Description] | [High/Medium/Low] |

### 2.4 Intended Use Environment

[Describe the intended operating environment of the software]

### 2.5 Assumptions and Constraints

**Assumptions**:
- [Assumption 1]

**Constraints**:
- [Constraint 1]

---

## 3. Functional Requirements

### 3.1 Requirements Overview

| ID | Requirement Name | Priority | Safety Class |
|----|------------------|----------|--------------|
| SRS-001 | [Requirement Name] | [High/Medium/Low] | [A/B/C] |
| SRS-002 | [Requirement Name] | [High/Medium/Low] | [A/B/C] |

### 3.2 Detailed Requirements

---

#### SRS-001 [Requirement Name]

| Attribute | Content |
|-----------|---------|
| **ID** | SRS-001 |
| **Name** | [Requirement Name] |
| **Description** | [The system shall...] |
| **Source** | [Source document or stakeholder] |
| **Priority** | [High/Medium/Low] |
| **Safety Class** | [Class A/B/C] |
| **Verification Method** | [Test/Analysis/Inspection/Demonstration] |
| **Preconditions** | [Preconditions] |
| **Postconditions** | [Postconditions] |
| **Related Requirements** | [Related SRS-xxx ID] |
| **SDD Traceability** | [Corresponding SCR-xxx ID] |

**Acceptance Criteria**:
1. [Criterion 1]
2. [Criterion 2]

**Notes**:
[Additional notes]

---

#### SRS-002 [Requirement Name]

| Attribute | Content |
|-----------|---------|
| **ID** | SRS-002 |
| **Name** | [Requirement Name] |
| **Description** | [The system shall...] |
| **Source** | [Source document or stakeholder] |
| **Priority** | [High/Medium/Low] |
| **Safety Class** | [Class A/B/C] |
| **Verification Method** | [Test/Analysis/Inspection/Demonstration] |
| **Preconditions** | [Preconditions] |
| **Postconditions** | [Postconditions] |
| **Related Requirements** | [Related SRS-xxx ID] |
| **SDD Traceability** | [Corresponding SCR-xxx ID] |

**Acceptance Criteria**:
1. [Criterion 1]

---

## 4. Non-Functional Requirements

### 4.1 Performance Requirements

#### SRS-NFR-001 [Performance Requirement Name]

| Attribute | Content |
|-----------|---------|
| **ID** | SRS-NFR-001 |
| **Type** | Performance |
| **Description** | [The system shall complete... within X seconds] |
| **Metric** | [Quantifiable standard] |
| **Verification Method** | [Test/Analysis] |

### 4.2 Security Requirements

#### SRS-NFR-002 [Security Requirement Name]

| Attribute | Content |
|-----------|---------|
| **ID** | SRS-NFR-002 |
| **Type** | Security |
| **Description** | [Describe security requirement] |
| **Verification Method** | [Test/Analysis/Inspection] |

### 4.3 Reliability Requirements

#### SRS-NFR-003 [Reliability Requirement Name]

| Attribute | Content |
|-----------|---------|
| **ID** | SRS-NFR-003 |
| **Type** | Reliability |
| **Description** | [Describe reliability requirement] |
| **MTBF** | [Mean Time Between Failures] |
| **Verification Method** | [Test/Analysis] |

### 4.4 Maintainability Requirements

#### SRS-NFR-004 [Maintainability Requirement Name]

| Attribute | Content |
|-----------|---------|
| **ID** | SRS-NFR-004 |
| **Type** | Maintainability |
| **Description** | [Describe maintainability requirement] |
| **Verification Method** | [Inspection/Analysis] |

---

## 5. Interface Requirements

### 5.1 User Interface Requirements

#### SRS-UI-001 [UI Requirement Name]

| Attribute | Content |
|-----------|---------|
| **ID** | SRS-UI-001 |
| **Description** | [Describe UI requirement] |
| **Related Screens** | [Screen name/ID] |

### 5.2 Hardware Interface Requirements

#### SRS-HW-001 [Hardware Interface Requirement Name]

| Attribute | Content |
|-----------|---------|
| **ID** | SRS-HW-001 |
| **Description** | [Describe hardware interface requirement] |
| **Protocol** | [Protocol name] |

### 5.3 Software Interface Requirements

#### SRS-SW-001 [Software Interface Requirement Name]

| Attribute | Content |
|-----------|---------|
| **ID** | SRS-SW-001 |
| **Description** | [Describe software interface requirement] |
| **API Specification** | [API description] |

### 5.4 Communication Interface Requirements

#### SRS-COM-001 [Communication Interface Requirement Name]

| Attribute | Content |
|-----------|---------|
| **ID** | SRS-COM-001 |
| **Description** | [Describe communication interface requirement] |
| **Protocol** | [Protocol name] |
| **Bandwidth Requirement** | [Requirement description] |

---

## 6. Software Safety Classification

### 6.1 Classification Basis

According to IEC 62304 standard, software safety classification is based on the severity of harm that may result from software failure:

| Classification | Definition | Applicable to This System |
|----------------|------------|---------------------------|
| Class A | No injury or damage to health | [Yes/No] |
| Class B | Non-serious injury possible | [Yes/No] |
| Class C | Death or serious injury possible | [Yes/No] |

### 6.2 System Classification

**Overall Software Safety Classification**: [Class A/B/C]

**Classification Rationale**:
[Explain why this classification was adopted]

### 6.3 Function-Level Safety Classification

| Function ID | Function Name | Safety Class | Classification Rationale |
|-------------|---------------|--------------|--------------------------|
| SRS-001 | [Name] | [A/B/C] | [Rationale] |

---

## 7. Appendix

### 7.1 Terminology Definitions

| Term | Definition |
|------|------------|
| [Term 1] | [Definition] |

### 7.2 Abbreviations

| Abbreviation | Full Name |
|--------------|-----------|
| SRS | Software Requirements Specification |
| IEC | International Electrotechnical Commission |

---

> **End of Document**
