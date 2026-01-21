# Requirements Traceability Matrix
## For {{project name}}

Version {{version}}
Prepared by {{author}}
{{organization}}
{{date}}

> ### 100% Traceability Requirement
>
> **All traceability directions must achieve 100% coverage:**
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
* [5. Coverage Analysis](#5-coverage-analysis)
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

| Document ID | Document Name | Version |
|-------------|---------------|---------|
| SRS-xxx | Software Requirements Specification | [Version] |
| SDD-xxx | Software Design Description | [Version] |
| SWD-xxx | Software Detailed Design | [Version] |
| STP-xxx | Software Test Plan | [Version] |
| STC-xxx | Software Test Cases | [Version] |
| SVV-xxx | Software Verification & Validation Report | [Version] |

---

## 2. Traceability Matrix Overview

### 2.1 Purpose

This traceability matrix is used for:
- Ensuring all requirements are implemented and verified
- Supporting change impact analysis
- Compliance with IEC 62304 traceability requirements
- Supporting regulatory review and audits

### 2.2 Traceability Levels

```
┌─────────────────────────────────────────────────────────────────┐
│                    Traceability Level Architecture              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  User Requirements  System Requirements  Software Requirements  │
│       URD     →         SYS        →         SRS              │
│                                              │                  │
│  Software Design   Detailed Design    Code                      │
│       SDD     →         SWD                                     │
│        │              │                │                        │
│        ↓              ↓                ↓                        │
│     Test Plan     Test Cases     Verification Report            │
│       STP     →      STC     →      SVV                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 Traceability Relationship Description

| Relationship | Description | Direction |
|--------------|-------------|-----------|
| SRS → SDD | Requirements implemented in design | Forward |
| SDD → SWD | Design implemented in code | Forward |
| SRS → STC | Requirements verified by tests | Forward |
| STC → SVV | Tests recorded in verification | Forward |
| SDD ← SRS | Design originates from requirements | Reverse |
| SWD ← SDD | Code originates from design | Reverse |

---

## 3. Complete Traceability Matrix

### 3.1 Functional Requirements Traceability Matrix

> **Each row must be complete; all fields cannot be empty (except NFR)**

| SRS ID | SRS Name | Safety Class | SDD ID | SWD ID | UI (SCR) ID | STC ID | SVV ID | Status |
|--------|----------|--------------|--------|--------|-------------|--------|--------|--------|
| SRS-AUTH-001 | [Requirement Name] | Class A | SDD-AUTH-001 | SWD-AUTH-001, 002 | SCR-AUTH-001 | STC-AUTH-001, 002 | SVV-006 | ✅ |
| SRS-AUTH-002 | [Requirement Name] | Class A | SDD-AUTH-002 | SWD-AUTH-003 | SCR-AUTH-002 | STC-AUTH-003 | SVV-006 | ✅ |
| SRS-TRAIN-001 | [Requirement Name] | Class B | SDD-TRAIN-001 | SWD-TRAIN-001, 002 | SCR-TRAIN-001 | STC-TRAIN-001, 002 | SVV-006 | ✅ |
| SRS-TRAIN-002 | [Requirement Name] | Class B | SDD-TRAIN-002 | SWD-TRAIN-003 | SCR-TRAIN-002 | STC-TRAIN-003 | SVV-006 | ✅ |
| SRS-REPORT-001 | [Requirement Name] | Class A | SDD-REPORT-001 | SWD-REPORT-001 | SCR-REPORT-001 | STC-REPORT-001, 002 | SVV-006 | ✅ |

**Status Legend:**
- ✅ Complete traceability (all fields have corresponding IDs)
- ⚠️ Partial traceability (missing some fields) - **Must be completed**
- ❌ No traceability - **Must be completed**

### 3.2 Non-Functional Requirements Traceability Matrix

| SRS ID | SRS Name | Type | SDD ID | STC ID | SVV ID | Status |
|--------|----------|------|--------|--------|--------|--------|
| SRS-NFR-001 | [Performance Requirement] | Performance | SDD-ARCH-001 | STC-PERF-001 | SVV-006 | Complete |
| SRS-NFR-002 | [Security Requirement] | Security | SDD-SEC-001 | STC-SEC-001 | SVV-006 | Complete |
| SRS-NFR-003 | [Reliability Requirement] | Reliability | SDD-REL-001 | STC-REL-001 | SVV-006 | Complete |

### 3.3 Interface Requirements Traceability Matrix

| SRS ID | SRS Name | Interface Type | SDD ID | SWD ID | STC ID | Status |
|--------|----------|----------------|--------|--------|--------|--------|
| SRS-UI-001 | [UI Requirement] | User Interface | SDD-UI-001 | SWD-UI-001 | STC-UI-001 | Complete |
| SRS-HW-001 | [Hardware Interface] | Hardware Interface | SDD-HW-001 | SWD-HW-001 | STC-HW-001 | Complete |
| SRS-SW-001 | [Software Interface] | Software Interface | SDD-SW-001 | SWD-SW-001 | STC-SW-001 | Complete |

---

## 4. Bidirectional Traceability Analysis

### 4.1 Forward Traceability (Requirements → Verification)

Verify that each requirement has corresponding design, detailed design, UI screen, and tests.

> **All fields must be ✓, partial traceability is not acceptable**

| SRS ID | → SDD | → SWD | → UI (SCR) | → STC | → SVV | Traceability Completeness |
|--------|-------|-------|------------|-------|-------|---------------------------|
| SRS-AUTH-001 | ✓ | ✓ | ✓ | ✓ | ✓ | ✅ Complete |
| SRS-AUTH-002 | ✓ | ✓ | ✓ | ✓ | ✓ | ✅ Complete |
| SRS-TRAIN-001 | ✓ | ✓ | ✓ | ✓ | ✓ | ✅ Complete |
| SRS-TRAIN-002 | ✓ | ✓ | ✓ | ✓ | ✓ | ✅ Complete |
| SRS-NFR-001 | ✓ | - | - | ✓ | ✓ | ✅ Complete (NFR has no UI) |

### 4.2 Reverse Traceability (Verification → Requirements)

Verify that each design, implementation, and test can be traced back to requirements.

#### 4.2.1 Design → Requirements

| SDD ID | SDD Name | ← SRS ID | Traceability Status |
|--------|----------|----------|---------------------|
| SDD-001 | [Design Name] | SRS-001 | Traced |
| SDD-002 | [Design Name] | SRS-002 | Traced |
| SDD-003 | [Design Name] | SRS-003 | Traced |

#### 4.2.2 Code → Design

| SWD ID | SWD Name | ← SDD ID | ← SRS ID | Traceability Status |
|--------|----------|----------|----------|---------------------|
| SWD-001 | [Code Name] | SDD-001 | SRS-001 | Traced |
| SWD-002 | [Code Name] | SDD-001 | SRS-001 | Traced |
| SWD-003 | [Code Name] | SDD-002 | SRS-002 | Traced |

#### 4.2.3 Tests → Requirements

| STC ID | STC Name | ← SRS ID | Traceability Status |
|--------|----------|----------|---------------------|
| STC-001 | [Test Name] | SRS-001 | Traced |
| STC-002 | [Test Name] | SRS-001 | Traced |
| STC-003 | [Test Name] | SRS-002 | Traced |

### 4.3 Orphan Item Analysis

#### 4.3.1 Items Without Traceability Source

| Item Type | ID | Name | Issue Description | Processing Status |
|-----------|-----|------|-------------------|-------------------|
| Design | - | - | No orphan designs | - |
| Code | - | - | No orphan code | - |
| Test | - | - | No orphan tests | - |

#### 4.3.2 Items Without Traceability Target

| Item Type | ID | Name | Missing Traceability | Processing Status |
|-----------|-----|------|---------------------|-------------------|
| Requirement | - | - | No gaps | - |

---

## 5. Coverage Analysis

### 5.1 Requirements Coverage Statistics

> **⚠️ All coverage rates must reach 100%**

| Coverage Type | Total | Covered | Uncovered | Coverage Rate | Requirement |
|---------------|-------|---------|-----------|---------------|-------------|
| SRS → SDD (Design) | [N] | [N] | 0 | 100% | **Must be 100%** |
| SRS → SWD (Detailed Design) | [N] | [N] | 0 | 100% | **Must be 100%** |
| SRS → UI (SCR) | [N] | [N] | 0 | 100% | **Must be 100%** |
| SRS → STC (Testing) | [N] | [N] | 0 | 100% | **Must be 100%** |
| SRS → SVV (Verification) | [N] | [N] | 0 | 100% | **Must be 100%** |

### 5.2 Design Coverage Statistics

| Coverage Type | Total | Covered | Uncovered | Coverage Rate | Requirement |
|---------------|-------|---------|-----------|---------------|-------------|
| SDD ← SRS | [N] | [N] | 0 | 100% | **Must be 100%** |
| SDD → SWD | [N] | [N] | 0 | 100% | **Must be 100%** |

### 5.3 Test Coverage Statistics

| Coverage Type | Total | Covered | Uncovered | Coverage Rate | Requirement |
|---------------|-------|---------|-----------|---------------|-------------|
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
     Req→Design  Req→Code  Req→Test  Overall
```

---

## 6. Change Impact Traceability

### 6.1 Change Impact Analysis Example

When requirements change, use this matrix to analyze impact scope:

**Example: SRS-001 Change Impact Analysis**

| Changed Requirement | Affected Design | Affected Code | Affected Tests | Re-verification |
|--------------------|-----------------|---------------|----------------|-----------------|
| SRS-001 | SDD-001 | SWD-001, SWD-002 | STC-001, STC-002 | SVV-006 |

**Impact Assessment**:
- Design changes: 1 item
- Code changes: 2 items
- Test updates: 2 items
- Re-verification: Yes

### 6.2 Change Traceability Records

| Change ID | Change Date | Changed Item | Impact Scope | Processing Status |
|-----------|-------------|--------------|--------------|-------------------|
| CHG-001 | [Date] | SRS-001 | SDD-001, SWD-001, STC-001 | Completed |
| CHG-002 | [Date] | SDD-002 | SWD-003, STC-003 | Completed |

### 6.3 Impact Scope Query

#### 6.3.1 Query Impact by Requirement

Input SRS ID to query all affected items:

```
Query: SRS-001
Result:
├── Design: SDD-001
│   └── Code: SWD-001, SWD-002
├── Tests: STC-001, STC-002
└── Verification: SVV-006
```

#### 6.3.2 Query Impact by Design

Input SDD ID to query upstream and downstream traceability:

```
Query: SDD-001
Result:
├── Upstream requirement: SRS-001
├── Downstream code: SWD-001, SWD-002
└── Related tests: STC-001, STC-002
```

---

## 7. Appendix

### 7.1 Traceability Matrix Maintenance Guide

**When adding new requirements** (must establish complete traceability chain):
1. Add requirement in SRS, assign SRS-{MODULE}-xxx ID
2. Create corresponding SDD-{MODULE}-xxx architecture design ← **Required**
3. Create corresponding SWD-{MODULE}-xxx detailed design ← **Required**
4. Create corresponding SCR-{MODULE}-xxx UI screen design ← **Required (for functional requirements)**
5. Create corresponding STC-{MODULE}-xxx test cases ← **Required**
6. Update this traceability matrix, confirm all coverage rates remain at 100%

> **⚠️ Any new requirement must simultaneously establish complete traceability chain; partial traceability is not acceptable**

**When changing requirements**:
1. Identify the changed SRS ID
2. Use Section 6 method to analyze impact
3. Update all affected documents
4. Update this traceability matrix
5. Re-execute affected tests

**When deleting requirements**:
1. Confirm requirement can be deleted
2. Mark related design, code, tests as deprecated
3. Update this traceability matrix
4. Record deletion reason

### 7.2 Traceability Status Definitions

| Status | Definition |
|--------|------------|
| Complete | Forward and reverse traceability are both complete |
| Partial | Some traceability relationships are missing |
| Missing | No traceability relationship |
| Pending | Traceability relationship to be confirmed |

### 7.3 Terminology Definitions

| Term | Definition |
|------|------------|
| Forward Traceability | Tracing from requirements to design, implementation, testing |
| Reverse Traceability | Tracing from testing, implementation, design back to requirements |
| Coverage Rate | Proportion of items with established traceability relationships |

### 7.4 Abbreviations

| Abbreviation | Full Name |
|--------------|-----------|
| RTM | Requirements Traceability Matrix |
| SRS | Software Requirements Specification |
| SDD | Software Design Description |
| SWD | Software Detailed Design |
| STC | Software Test Case |
| SVV | Software Verification & Validation |

---

## Sign-off

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Author | | | |
| Reviewer | | | |
| Approver | | | |
