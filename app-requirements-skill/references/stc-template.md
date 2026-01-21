# Software Test Cases
## For {{project name}}

Version {{version}}
Prepared by {{author}}
{{organization}}
{{date}}

## Table of Contents
<!-- TOC -->
* [1. Introduction](#1-introduction)
* [2. Test Case List](#2-test-case-list)
* [3. Test Case Details](#3-test-case-details)
* [4. Test Execution Records](#4-test-execution-records)
* [5. Appendix](#5-appendix)
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
| STP-xxx | Software Test Plan | [Version] |

### 1.3 Test Coverage Traceability

| Requirement ID | Test Case ID | Coverage Status |
|----------------|--------------|-----------------|
| SRS-001 | STC-001, STC-002 | Fully covered |
| SRS-002 | STC-003 | Fully covered |
| SRS-003 | STC-004, STC-005 | Fully covered |

---

## 2. Test Case List

### 2.1 Test Case Overview

| ID | Name | Related Requirement | Related Design | Test Type | Priority | Status |
|----|------|---------------------|----------------|-----------|----------|--------|
| STC-001 | [Test Case Name] | SRS-001 | SDD-001 | Functional | High | [Not Executed/Pass/Fail] |
| STC-002 | [Test Case Name] | SRS-001 | SDD-001 | Boundary | High | [Not Executed/Pass/Fail] |
| STC-003 | [Test Case Name] | SRS-002 | SDD-002 | Functional | Medium | [Not Executed/Pass/Fail] |
| STC-004 | [Test Case Name] | SRS-NFR-001 | - | Performance | High | [Not Executed/Pass/Fail] |
| STC-005 | [Test Case Name] | SRS-003 | SDD-003 | Exception | Medium | [Not Executed/Pass/Fail] |

### 2.2 Test Case Classification Statistics

| Test Type | Count | Pass | Fail | Not Executed |
|-----------|-------|------|------|--------------|
| Functional | [Count] | [Count] | [Count] | [Count] |
| Boundary | [Count] | [Count] | [Count] | [Count] |
| Exception | [Count] | [Count] | [Count] | [Count] |
| Performance | [Count] | [Count] | [Count] | [Count] |
| **Total** | [Count] | [Count] | [Count] | [Count] |

---

## 3. Test Case Details

---

### STC-001 [Test Case Name]

| Attribute | Content |
|-----------|---------|
| **ID** | STC-001 |
| **Name** | [Test Case Name] |
| **Related Requirement** | SRS-001 |
| **Related Design** | SDD-001 |
| **Related Test Strategy** | STP-003 |
| **Test Type** | Functional |
| **Priority** | High |
| **Automated** | [Yes/No] |

**Test Purpose**:
[Describe the objective this test case is verifying]

**Preconditions**:
1. [Condition 1: e.g., System is started]
2. [Condition 2: e.g., User is logged in]
3. [Condition 3: e.g., Test data is prepared]

**Test Data**:
| Data Item | Value | Description |
|-----------|-------|-------------|
| [Data 1] | [Value] | [Description] |
| [Data 2] | [Value] | [Description] |

**Test Steps**:

| Step | Action | Input Data | Expected Result |
|------|--------|------------|-----------------|
| 1 | [Action description] | [Input value] | [Expected output/state] |
| 2 | [Action description] | [Input value] | [Expected output/state] |
| 3 | [Action description] | [Input value] | [Expected output/state] |
| 4 | [Action description] | - | [Expected output/state] |

**Postconditions**:
1. [Cleanup action 1]
2. [Cleanup action 2]

**Acceptance Criteria**:
- [ ] All step actual results match expected results
- [ ] No unexpected error messages
- [ ] System state is correct

---

### STC-002 [Test Case Name - Boundary Test]

| Attribute | Content |
|-----------|---------|
| **ID** | STC-002 |
| **Name** | [Test Case Name] |
| **Related Requirement** | SRS-001 |
| **Related Design** | SDD-001 |
| **Related Test Strategy** | STP-003 |
| **Test Type** | Boundary |
| **Priority** | High |
| **Automated** | [Yes/No] |

**Test Purpose**:
Verify [feature name] behaves correctly under boundary value conditions

**Preconditions**:
1. [Condition description]

**Boundary Value Test Data**:
| Test Scenario | Input Value | Expected Result | Description |
|---------------|-------------|-----------------|-------------|
| Minimum value | [min] | [Expected] | Lower bound test |
| Minimum value - 1 | [min-1] | [Error] | Below lower bound |
| Maximum value | [max] | [Expected] | Upper bound test |
| Maximum value + 1 | [max+1] | [Error] | Above upper bound |
| Typical value | [typical] | [Expected] | Normal range |

**Test Steps**:

| Step | Action | Input Data | Expected Result |
|------|--------|------------|-----------------|
| 1 | Enter minimum value | [min] | System accepts, processes correctly |
| 2 | Enter below minimum | [min-1] | Display error message |
| 3 | Enter maximum value | [max] | System accepts, processes correctly |
| 4 | Enter above maximum | [max+1] | Display error message |

---

### STC-003 [Test Case Name]

| Attribute | Content |
|-----------|---------|
| **ID** | STC-003 |
| **Name** | [Test Case Name] |
| **Related Requirement** | SRS-002 |
| **Related Design** | SDD-002 |
| **Related Test Strategy** | STP-003 |
| **Test Type** | Functional |
| **Priority** | Medium |
| **Automated** | [Yes/No] |

**Test Purpose**:
[Describe the objective this test case is verifying]

**Preconditions**:
1. [Condition description]

**Test Steps**:

| Step | Action | Input Data | Expected Result |
|------|--------|------------|-----------------|
| 1 | [Action description] | [Input value] | [Expected output/state] |
| 2 | [Action description] | [Input value] | [Expected output/state] |

---

### STC-004 [Performance Test Case]

| Attribute | Content |
|-----------|---------|
| **ID** | STC-004 |
| **Name** | [Performance Test Case Name] |
| **Related Requirement** | SRS-NFR-001 |
| **Related Design** | - |
| **Related Test Strategy** | STP-003 |
| **Test Type** | Performance |
| **Priority** | High |
| **Automated** | Yes |

**Test Purpose**:
Verify system performance meets requirements specification

**Performance Metrics**:
| Metric | Required Value | Measurement Method |
|--------|----------------|-------------------|
| Response time | < [X] ms | Average |
| Throughput | > [Y] TPS | Transactions per second |
| Resource usage | < [Z]% CPU | Peak |

**Test Conditions**:
| Item | Setting |
|------|---------|
| Concurrent users | [Count] |
| Test duration | [Time] |
| Data volume | [Record count] |

**Test Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Set up test environment and tools | Environment ready |
| 2 | Execute load test | Record performance data |
| 3 | Collect performance metrics | Generate performance report |
| 4 | Compare against requirements | All metrics meet requirements |

---

### STC-005 [Exception Test Case]

| Attribute | Content |
|-----------|---------|
| **ID** | STC-005 |
| **Name** | [Exception Test Case Name] |
| **Related Requirement** | SRS-003 |
| **Related Design** | SDD-003 |
| **Related Test Strategy** | STP-003 |
| **Test Type** | Exception |
| **Priority** | Medium |
| **Automated** | [Yes/No] |

**Test Purpose**:
Verify system's ability to handle abnormal conditions

**Exception Scenarios**:
| Scenario ID | Exception Description | Trigger Method | Expected Behavior |
|-------------|----------------------|----------------|-------------------|
| EXC-01 | Invalid input | Enter special characters | Display error message |
| EXC-02 | Network interruption | Disconnect network | Display connection error |
| EXC-03 | Database unresponsive | Stop database | Activate backup mechanism |

**Test Steps**:

| Step | Action | Input Data | Expected Result |
|------|--------|------------|-----------------|
| 1 | Trigger exception scenario | [Exception input] | System detects exception |
| 2 | Observe system response | - | Display appropriate error message |
| 3 | Confirm system stability | - | System does not crash |
| 4 | Restore normal state | - | System resumes normal operation |

---

## 4. Test Execution Records

### 4.1 Execution Summary

| Test Round | Execution Date | Executor | Pass | Fail | Blocked | Total |
|------------|----------------|----------|------|------|---------|-------|
| Round 1 | [Date] | [Name] | [Count] | [Count] | [Count] | [Count] |
| Round 2 | [Date] | [Name] | [Count] | [Count] | [Count] | [Count] |

### 4.2 Detailed Test Execution Records

---

#### STC-001 Execution Record

| Attribute | Content |
|-----------|---------|
| **Test Case ID** | STC-001 |
| **Execution Date** | [YYYY-MM-DD] |
| **Executor** | [Name] |
| **Test Environment** | [Environment Name] |
| **Execution Result** | [Pass/Fail/Blocked] |

**Step Execution Results**:

| Step | Expected Result | Actual Result | Status |
|------|-----------------|---------------|--------|
| 1 | [Expected] | [Actual] | [Pass/Fail] |
| 2 | [Expected] | [Actual] | [Pass/Fail] |
| 3 | [Expected] | [Actual] | [Pass/Fail] |
| 4 | [Expected] | [Actual] | [Pass/Fail] |

**Test Evidence**:
- Screenshots: [File path/link]
- Logs: [File path/link]

**Notes**:
[Additional notes]

**Related Defects**:
| Defect ID | Description | Status |
|-----------|-------------|--------|
| [BUG-xxx] | [Description] | [Open/Fixed/Closed] |

---

#### STC-002 Execution Record

| Attribute | Content |
|-----------|---------|
| **Test Case ID** | STC-002 |
| **Execution Date** | [YYYY-MM-DD] |
| **Executor** | [Name] |
| **Test Environment** | [Environment Name] |
| **Execution Result** | [Pass/Fail/Blocked] |

**Step Execution Results**:

| Step | Expected Result | Actual Result | Status |
|------|-----------------|---------------|--------|
| 1 | [Expected] | [Actual] | [Pass/Fail] |
| 2 | [Expected] | [Actual] | [Pass/Fail] |

---

## 5. Appendix

### 5.1 Test Conclusion Summary

| Item | Result |
|------|--------|
| Total test cases | [Count] |
| Passed | [Count] |
| Failed | [Count] |
| Pass rate | [Percentage]% |
| Requirement coverage | [Percentage]% |

### 5.2 Terminology Definitions

| Term | Definition |
|------|------------|
| Pass | Test case execution result matches expected |
| Fail | Test case execution result does not match expected |
| Block | Test cannot be executed due to external factors |

### 5.3 Abbreviations

| Abbreviation | Full Name |
|--------------|-----------|
| STC | Software Test Case |
| TPS | Transactions Per Second |

---

## Sign-off

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Author | | | |
| Reviewer | | | |
| Approver | | | |
