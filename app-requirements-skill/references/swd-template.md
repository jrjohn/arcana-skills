# Software Detailed Design
## For {{project name}}

Version {{version}}
Prepared by {{author}}
{{organization}}
{{date}}

## Table of Contents
<!-- TOC -->
* [1. Introduction](#1-introduction)
* [2. Module Detailed Design](#2-module-detailed-design)
* [3. Algorithm Description](#3-algorithm-description)
* [4. Data Structure Definition](#4-data-structure-definition)
* [5. Error Handling](#5-error-handling)
* [6. Appendix](#6-appendix)
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

### 1.3 Traceability Mapping

| Detailed Design ID | Corresponding Design ID | Corresponding Requirement ID |
|--------------------|------------------------|------------------------------|
| SWD-001 | SDD-001 | SRS-001 |
| SWD-002 | SDD-001 | SRS-001 |
| SWD-003 | SDD-002 | SRS-002 |

---

## 2. Module Detailed Design

### 2.1 Detailed Design Overview

| ID | Name | Corresponding Design | Safety Class | Source File |
|----|------|---------------------|--------------|-------------|
| SWD-001 | [Name] | SDD-001 | [A/B/C] | [File path] |
| SWD-002 | [Name] | SDD-001 | [A/B/C] | [File path] |

### 2.2 Detailed Design Description

---

#### SWD-001 [Function/Class Name]

| Attribute | Content |
|-----------|---------|
| **ID** | SWD-001 |
| **Name** | [Function/Class Name] |
| **Corresponding Design** | SDD-001 |
| **Corresponding Requirement** | SRS-001 |
| **Safety Class** | [Class A/B/C] |
| **Source File** | [src/module/file.ts] |
| **Type** | [Function/Class/Interface] |

**Function Signature**:
```typescript
/**
 * [Function description]
 * @param param1 - [Parameter 1 description]
 * @param param2 - [Parameter 2 description]
 * @returns [Return value description]
 * @throws [Exception description]
 */
function functionName(param1: Type1, param2: Type2): ReturnType
```

**Parameter Description**:
| Parameter | Type | Required | Default | Description | Valid Range |
|-----------|------|----------|---------|-------------|-------------|
| param1 | Type1 | Y | - | [Description] | [Range] |
| param2 | Type2 | N | null | [Description] | [Range] |

**Return Value**:
| Type | Description | Possible Values |
|------|-------------|-----------------|
| ReturnType | [Description] | [Possible values] |

**Processing Flow**:
```
Start
  │
  ▼
┌─────────────────┐
│ 1. Validate input │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 2. Execute logic │
└────────┬────────┘
         │
         ▼
    ┌────┴────┐
    │ Success? │
    └────┬────┘
   Yes ／ ＼ No
      ▼     ▼
┌─────┐ ┌─────────┐
│Return│ │Throw    │
│value │ │exception│
└─────┘ └─────────┘
```

**Pseudocode**:
```
FUNCTION functionName(param1, param2)
    // Step 1: Validate input
    IF param1 is invalid THEN
        THROW InvalidParameterException
    END IF

    // Step 2: Execute business logic
    result = processData(param1)

    // Step 3: Return result
    RETURN result
END FUNCTION
```

**Dependencies**:
| Dependency Item | Type | Description |
|-----------------|------|-------------|
| SWD-002 | Function call | Calls processData function |
| [Library] | External library | Uses xxx functionality |

---

#### SWD-002 [Function/Class Name]

| Attribute | Content |
|-----------|---------|
| **ID** | SWD-002 |
| **Name** | [Function/Class Name] |
| **Corresponding Design** | SDD-001 |
| **Corresponding Requirement** | SRS-001 |
| **Safety Class** | [Class A/B/C] |
| **Source File** | [src/module/file.ts] |
| **Type** | [Function/Class/Interface] |

**Class Definition**:
```typescript
/**
 * [Class description]
 */
class ClassName {
    // Properties
    private property1: Type1;
    public property2: Type2;

    // Constructor
    constructor(param1: Type1) {
        this.property1 = param1;
    }

    // Methods
    public method1(): ReturnType {
        // ...
    }
}
```

**Property Description**:
| Property | Type | Access Modifier | Description |
|----------|------|-----------------|-------------|
| property1 | Type1 | private | [Description] |
| property2 | Type2 | public | [Description] |

**Method Description**:
| Method | Parameters | Return Value | Description |
|--------|------------|--------------|-------------|
| method1() | - | ReturnType | [Description] |
| method2(p1) | Type1 | void | [Description] |

---

## 3. Algorithm Description

### 3.1 Algorithm Overview

| ID | Name | Used In | Complexity |
|----|------|---------|------------|
| ALG-001 | [Algorithm Name] | SWD-001 | O(n) |

### 3.2 Detailed Algorithm Description

---

#### ALG-001 [Algorithm Name]

| Attribute | Content |
|-----------|---------|
| **ID** | ALG-001 |
| **Name** | [Algorithm Name] |
| **Used In** | SWD-001, SWD-003 |
| **Time Complexity** | O(n) |
| **Space Complexity** | O(1) |

**Algorithm Description**:
[Describe the purpose and principles of the algorithm]

**Pseudocode**:
```
ALGORITHM algorithmName(input)
    INPUT: [Input description]
    OUTPUT: [Output description]

    FOR i = 0 TO length(input) - 1
        // Step 1: [Step description]
        process(input[i])

        // Step 2: [Step description]
        IF condition THEN
            result = compute(input[i])
        END IF
    END FOR

    RETURN result
END ALGORITHM
```

**Example**:
```
Input: [1, 2, 3, 4, 5]
Processing:
  i=0: process(1) → result=1
  i=1: process(2) → result=3
  ...
Output: 15
```

---

## 4. Data Structure Definition

### 4.1 Data Structure Overview

| ID | Name | Type | Used In |
|----|------|------|---------|
| DS-001 | [Structure Name] | Interface | SWD-001 |
| DS-002 | [Structure Name] | Enum | SWD-002 |

### 4.2 Detailed Data Structure Definition

---

#### DS-001 [Structure Name]

| Attribute | Content |
|-----------|---------|
| **ID** | DS-001 |
| **Name** | [Structure Name] |
| **Type** | Interface |
| **Used In** | SWD-001, SWD-002 |

**Definition**:
```typescript
interface IDataStructure {
    id: string;           // Unique identifier
    name: string;         // Name
    value: number;        // Value
    status: StatusEnum;   // Status
    createdAt: Date;      // Creation time
    metadata?: object;    // Optional metadata
}
```

**Field Description**:
| Field | Type | Required | Description | Validation Rules |
|-------|------|----------|-------------|------------------|
| id | string | Y | Unique identifier | UUID format |
| name | string | Y | Name | 1-100 characters |
| value | number | Y | Value | >= 0 |
| status | StatusEnum | Y | Status | See DS-002 |
| createdAt | Date | Y | Creation time | ISO 8601 |
| metadata | object | N | Metadata | - |

---

#### DS-002 [Enum Name]

| Attribute | Content |
|-----------|---------|
| **ID** | DS-002 |
| **Name** | StatusEnum |
| **Type** | Enum |
| **Used In** | DS-001, SWD-001 |

**Definition**:
```typescript
enum StatusEnum {
    PENDING = 'PENDING',       // Pending
    PROCESSING = 'PROCESSING', // Processing
    COMPLETED = 'COMPLETED',   // Completed
    FAILED = 'FAILED'          // Failed
}
```

**Value Description**:
| Value | Description | Transition Rules |
|-------|-------------|------------------|
| PENDING | Pending | Initial state |
| PROCESSING | Processing | Transitions from PENDING |
| COMPLETED | Completed | Transitions from PROCESSING |
| FAILED | Failed | Transitions from PROCESSING |

---

## 5. Error Handling Mechanism

### 5.1 Error Code Definition

| Error Code | Name | Description | Severity |
|------------|------|-------------|----------|
| E001 | InvalidParameter | Invalid input parameter | Warning |
| E002 | DataNotFound | Data not found | Warning |
| E003 | ProcessingError | Error during processing | Error |
| E004 | SystemFailure | System failure | Critical |

### 5.2 Exception Handling Strategy

---

#### 5.2.1 Input Validation Error

| Attribute | Content |
|-----------|---------|
| **Error Code** | E001 |
| **Occurrence Location** | SWD-001, SWD-002 |
| **Handling Method** | Return error message, do not interrupt system |
| **Log Level** | Warning |

**Handling Flow**:
```
1. Catch InvalidParameterException
2. Log error information (parameter name, value passed, expected format)
3. Return standardized error response
4. Continue accepting subsequent requests
```

---

#### 5.2.2 System Failure

| Attribute | Content |
|-----------|---------|
| **Error Code** | E004 |
| **Occurrence Location** | System-wide |
| **Handling Method** | Safe shutdown procedure |
| **Log Level** | Critical |

**Handling Flow**:
```
1. Catch SystemFailureException
2. Immediately log complete error stack
3. Save current state (if possible)
4. Send alert notification
5. Execute safe shutdown procedure
```

### 5.3 Error Recovery Mechanism

| Error Type | Recovery Strategy | Max Retries | Retry Interval |
|------------|-------------------|-------------|----------------|
| Network timeout | Auto retry | 3 | 1 second |
| Database connection | Reconnect | 5 | 2 seconds |
| External service | Graceful degradation | 2 | 5 seconds |

---

## 6. Appendix

### 6.1 Coding Standards

| Item | Standard |
|------|----------|
| Naming convention | camelCase (variables), PascalCase (classes) |
| Indentation | 2 spaces |
| Line width limit | 100 characters |
| Comment language | English |

### 6.2 Terminology Definitions

| Term | Definition |
|------|------------|
| [Term] | [Definition] |

### 6.3 Abbreviations

| Abbreviation | Full Name |
|--------------|-----------|
| SWD | Software Detailed Design |
| ALG | Algorithm |
| DS | Data Structure |

---

## Sign-off

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Author | | | |
| Reviewer | | | |
| Approver | | | |
