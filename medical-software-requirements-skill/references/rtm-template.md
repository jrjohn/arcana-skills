# Requirements Traceability Matrix
## For {{project name}}

Version {{version}}
Prepared by {{author}}
{{organization}}
{{date}}

> ### 100% Traceability Requirement
>
> **All traceability directions must achieve 100% Coverage:**
>
> | Direction | Required |
> |-----------|----------|
> | SRS → SDD | **100%** |
> | SRS → SWD | **100%** |
> | SRS → STC | **100%** |
> | SRS → UI (SCR) | **100%** |
> | SDD → SWD | **100%** |
> | SWD → STC | **100%** |
>
> **If any direction is below 100%, missing items must be added until full traceability is achieved.**

## Table of Contents
<!-- TOC -->
* [1. Introduction](#1-introduction)
* [2. Traceability Matrix Overview](#2-traceability-matrix-overview)
* [3. Complete Traceability Matrix](#3-complete-traceability-matrix)
* [4. Bidirectional Traceability Analysis](#4-bidirectional-traceability-analysis)
* [5. Coverage Analysis](#5-Coverage-analysis)
* [6. Change Impact Traceability](#6-change-impact-traceability)
* [7. Appendix](#7-appendix)
<!-- TOC -->

## Revision History

| Name | Date | Reason For Changes | Version |
|------|------|--------------------|---------|
|      |      |                    |         |

---

## 1. Introduction

### 1.1 References

| Document Number | Document Name | Version |
|---------|---------|------|
| SRS-xxx | Software Requirements Specification | [Version] |
| SDD-xxx | Software Design Specification | [Version] |
| SWD-xxx | Software Detailed Design | [Version] |
| STP-xxx | Software Test Plan | [Version] |
| STC-xxx | Software Test Cases | [Version] |
| SVV-xxx | Software Verification & Validation Report | [Version] |

---

## 2. Traceability Matrix Overview

### 2.1 Traceability Objective

This traceability matrix is used to:
- Ensure all requirements are implemented and verified
- Support change impact analysis
- Align with IEC 62304 traceability requirements
- Support regulatory review and audit

### 2.2 Traceability Level

```
┌─────────────────────────────────────────────────────────────────┐
│                   Traceability Level Architecture                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  User Req.    System Req.    Software Req.    Design    Code   │
│     URD   →      SYS    →     SRS    →     SDD    →    SWD    │
│                                 │            │           │      │
│                                 ↓            ↓           ↓      │
│                           Test Plan    Test Cases    Verification│
│                               STP    →    STC    →    SVV      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 Traceability Relationship Description

| Traceability Relationship | Description | Direction |
|---------|------|------|
| SRS → SDD | Requirement realized in design | Forward |
| SDD → SWD | Design realized in implementation | Forward |
| SRS → STC | Requirement verified in test | Forward |
| STC → SVV | Test recorded in verification | Forward |
| SDD ← SRS | Design derived from requirement | Backward |
| SWD ← SDD | Implementation derived from design | Backward |

---

## 3. Complete Traceability Matrix

### 3.1 Functional Requirement Traceability Matrix

> **Every row must be filled completely. All fields must not be empty (except NFR)**

| SRS ID | SRS Name | Safety Classification | SDD ID | SWD ID | UI (SCR) ID | STC ID | SVV ID | Status |
|--------|---------|---------|--------|--------|-------------|--------|--------|------|
| SRS-AUTH-001 | [Requirement Name] | Class A | SDD-AUTH-001 | SWD-AUTH-001, 002 | SCR-AUTH-001 | STC-AUTH-001, 002 | SVV-006 | ✅ |
| SRS-AUTH-002 | [Requirement Name] | Class A | SDD-AUTH-002 | SWD-AUTH-003 | SCR-AUTH-002 | STC-AUTH-003 | SVV-006 | ✅ |
| SRS-TRAIN-001 | [Requirement Name] | Class B | SDD-TRAIN-001 | SWD-TRAIN-001, 002 | SCR-TRAIN-001 | STC-TRAIN-001, 002 | SVV-006 | ✅ |
| SRS-TRAIN-002 | [Requirement Name] | Class B | SDD-TRAIN-002 | SWD-TRAIN-003 | SCR-TRAIN-002 | STC-TRAIN-003 | SVV-006 | ✅ |
| SRS-REPORT-001 | [Requirement Name] | Class A | SDD-REPORT-001 | SWD-REPORT-001 | SCR-REPORT-001 | STC-REPORT-001, 002 | SVV-006 | ✅ |

**Status Description：**
- ✅ Complete traceability (All fields have corresponding IDs)
- ⚠️ Partial traceability (Some fields missing) - **Must be supplemented**
- ❌ No traceability - **Must be supplemented**

### 3.2 Non-Functional Requirements Traceability Matrix

| SRS ID | SRS Name | Type | SDD ID | STC ID | SVV ID | Status |
|--------|---------|------|--------|--------|--------|------|
| SRS-NFR-001 | [Performance Requirement] | Performance | SDD-ARCH-001 | STC-PERF-001 | SVV-006 | Complete |
| SRS-NFR-002 | [Security Requirement] | Security | SDD-SEC-001 | STC-SEC-001 | SVV-006 | Complete |
| SRS-NFR-003 | [Reliability Requirement] | Reliability | SDD-REL-001 | STC-REL-001 | SVV-006 | Complete |

### 3.3 Interface Requirements Traceability Matrix

| SRS ID | SRS Name | Interface Type | SDD ID | SWD ID | STC ID | Status |
|--------|---------|---------|--------|--------|--------|------|
| SRS-UI-001 | [UI Requirement] | User Interface | SDD-UI-001 | SWD-UI-001 | STC-UI-001 | Complete |
| SRS-HW-001 | [Hardware Interface] | Hardware Interface | SDD-HW-001 | SWD-HW-001 | STC-HW-001 | Complete |
| SRS-SW-001 | [Software Interface] | Software Interface | SDD-SW-001 | SWD-SW-001 | STC-SW-001 | Complete |

---

## 4. Bidirectional Traceability Analysis

### 4.1 Forward Traceability (Requirement → Validation)

Validate that each requirement has corresponding design, detailed design, UI screen, and test.

> **All fields must be ✓. Partial traceability is not accepted**

| SRS ID | → SDD | → SWD | → UI (SCR) | → STC | → SVV | Traceability Completeness |
|--------|-------|-------|------------|-------|-------|-----------|
| SRS-AUTH-001 | ✓ | ✓ | ✓ | ✓ | ✓ | ✅ Complete |
| SRS-AUTH-002 | ✓ | ✓ | ✓ | ✓ | ✓ | ✅ Complete |
| SRS-TRAIN-001 | ✓ | ✓ | ✓ | ✓ | ✓ | ✅ Complete |
| SRS-TRAIN-002 | ✓ | ✓ | ✓ | ✓ | ✓ | ✅ Complete |
| SRS-NFR-001 | ✓ | - | - | ✓ | ✓ | ✅ Complete (NFR None UI) |

### 4.2 Backward Traceability (Validation → Requirement)

Verify that each design, implementation, and test can be traced back to requirements.

#### 4.2.1 Design → Requirement

| SDD ID | SDD Name | ← SRS ID | Traceability Status |
|--------|---------|---------|---------|
| SDD-001 | [Design Name] | SRS-001 | Already Traced |
| SDD-002 | [Design Name] | SRS-002 | Already Traced |
| SDD-003 | [Design Name] | SRS-003 | Already Traced |

#### 4.2.2 Implementation → Design

| SWD ID | SWD Name | ← SDD ID | ← SRS ID | Traceability Status |
|--------|---------|---------|---------|---------|
| SWD-001 | [ImplementationName] | SDD-001 | SRS-001 | Already Traced |
| SWD-002 | [ImplementationName] | SDD-001 | SRS-001 | Already Traced |
| SWD-003 | [ImplementationName] | SDD-002 | SRS-002 | Already Traced |

#### 4.2.3 Test → Requirement

| STC ID | STC Name | ← SRS ID | Traceability Status |
|--------|---------|---------|---------|
| STC-001 | [TestName] | SRS-001 | Already Traced |
| STC-002 | [TestName] | SRS-001 | Already Traced |
| STC-003 | [TestName] | SRS-002 | Already Traced |

### 4.3 Orphan Items Analysis

#### 4.3.1 Items Without Traceability Source

| Item Type | ID | Name | Problem Description | Processing Status |
|---------|-----|------|---------|---------|
| Design | - | - | No orphan design | - |
| Implementation | - | - | No orphan implementation | - |
| Test | - | - | No orphan test | - |

#### 4.3.2 Items Without Traceability Target

| Item Type | ID | Name | Missing traceability | Processing Status |
|---------|-----|------|---------|---------|
| Requirement | - | - | No missing items | - |

---

## 5. Coverage Analysis

### 5.1 Requirement Coverage Statistics

> **⚠️ All Coverage must reach 100%**

| Coverage Type | Total Count | Covered | Not Covered | Coverage | Requirements |
|---------|------|--------|--------|--------|------|
| SRS → SDD (Design) | [N] | [N] | 0 | 100% | **Must be 100%** |
| SRS → SWD (Detailed Design) | [N] | [N] | 0 | 100% | **Must be 100%** |
| SRS → UI (SCR) | [N] | [N] | 0 | 100% | **Must be 100%** |
| SRS → STC (Test) | [N] | [N] | 0 | 100% | **Must be 100%** |
| SRS → SVV (Validate) | [N] | [N] | 0 | 100% | **Must be 100%** |

### 5.2 Design Coverage Statistics

| Coverage Type | Total Count | Covered | Not Covered | Coverage | Requirements |
|---------|------|--------|--------|--------|------|
| SDD ← SRS | [N] | [N] | 0 | 100% | **Must be 100%** |
| SDD → SWD | [N] | [N] | 0 | 100% | **Must be 100%** |

### 5.3 Test Coverage Statistics

| Coverage Type | Total Count | Covered | Not Covered | Coverage | Requirements |
|---------|------|--------|--------|--------|------|
| STC ← SRS | [N] | [N] | 0 | 100% | **Must be 100%** |
| SWD → STC | [N] | [N] | 0 | 100% | **Must be 100%** |
| STC → SVV | [N] | [N] | 0 | 100% | **Must be 100%** |

### 5.4 Coverage Trend Chart

```
Coverage (%)
100 ┤ ████████████████████████████████ 100%
 90 ┤
 80 ┤
 70 ┤
 60 ┤
 50 ┤
 40 ┤
 30 ┤
 20 ┤
 10 ┤
  0 ┼─────────────────────────────────
     Requirement→Design  Requirement→Implementation  Requirement→Test  Overall
```

---

## 6. Change Impact Traceability

### 6.1 Change Impact Analysis Example

When requirements change, use this matrix to analyze impact scope:

**Example: SRS-001 Change Impact Analysis**

| Changed Requirement | Impacted Design | Impacted Implementation | Impacted Test | Re-verification |
|---------|-----------|-----------|-----------|---------|
| SRS-001 | SDD-001 | SWD-001, SWD-002 | STC-001, STC-002 | SVV-006 |

**Impact assessment**:
- Design changes: 1 item
- Implementation changes: 2 items
- Test updates: 2 items
- Verification redo: Yes

### 6.2 Change Traceability Record

| Change ID | Change Date | Changed Items | Impact Scope | Processing Status |
|--------|---------|---------|---------|---------|
| CHG-001 | [Date] | SRS-001 | SDD-001, SWD-001, STC-001 | Completed |
| CHG-002 | [Date] | SDD-002 | SWD-003, STC-003 | Completed |

### 6.3 Impact Scope Query

#### 6.3.1 Query impact from dependent requirement

Input SRS ID, query all impacted items:

```
Query: SRS-001
Results:
├── Design: SDD-001
│   └── Implementation: SWD-001, SWD-002
├── Test: STC-001, STC-002
└── Validation: SVV-006
```

#### 6.3.2 Query impact from dependent design

Input SDD ID, query upstream/downstream traceability:

```
Query: SDD-001
Results:
├── Upstream requirement: SRS-001
├── Downstream implementation: SWD-001, SWD-002
└── Related test: STC-001, STC-002
```

---

## 7. Appendix

### 7.1 Traceability Matrix Maintenance Guide

**When adding requirement** (Must create complete traceability chain):
1. Add requirement in SRS, allocate SRS-{MODULE}-xxx ID
2. Create corresponding SDD-{MODULE}-xxx Architecture Design ← **Required**
3. Create corresponding SWD-{MODULE}-xxx Detailed Design ← **Required**
4. Create corresponding SCR-{MODULE}-xxx UI Screen Design ← **Required (Functional Requirement)**
5. Create corresponding STC-{MODULE}-xxx Test Cases ← **Required**
6. Update this traceability matrix, confirm all coverage maintains 100%

> **⚠️ Any new requirement must simultaneously create complete traceability chain. Partial traceability is not accepted**

**When requirement changes**:
1. Identify the changed SRS ID
2. Use section 6 method to analyze impact
3. Update all impacted documents
4. Update this traceability matrix
5. Re-execute impacted tests

**When deleting requirement**：
1. Confirm requirement can be deleted
2. Mark related design、Implementation、Test as deprecated
3. Update this traceability matrix
4. Record deletion reason

### 7.2 Traceability Status Definition

| Status | Definition |
|-----|------|
| Complete | Both forward and backward traceability are complete |
| Partial | Partial traceability relationship missing |
| Missing | No traceability relationship |
| Pending confirmation | Traceability relationship pending confirmation |

### 7.3 Technical Terms Definition

| Technical Term | Definition |
|-----|------|
| Forward Traceability | From requirement traced to design, implementation, test |
| Backward Traceability | From test, implementation, design traced back to requirement |
| Coverage | Ratio of items with established traceability relationships |

### 7.4 Abbreviations

| Abbreviations | Full Name |
|-----|------|
| RTM | Requirements Traceability Matrix |
| SRS | Software Requirements Specification |
| SDD | Software Design Description |
| SWD | Software Detailed Design |
| STC | Software Test Case |
| SVV | Software Verification & Validation |

---

## Approval

| Role | Name | Signature | Date |
|-----|------|------|------|
| Author | | | |
| Reviewer | | | |
| Approver | | | |
