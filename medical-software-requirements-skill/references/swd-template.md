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

| 文件編號 | 文件名稱 | 版本 |
|---------|---------|------|
| SRS-xxx | 軟體需求規格書 | [版本] |
| SDD-xxx | 軟體設計規格書 | [版本] |

### 1.3 追溯對照表

| 詳細設計 ID | 對應設計 ID | 對應需求 ID |
|------------|------------|------------|
| SWD-001 | SDD-001 | SRS-001 |
| SWD-002 | SDD-001 | SRS-001 |
| SWD-003 | SDD-002 | SRS-002 |

---

## 2. 模組詳細設計

### 2.1 詳細設計總覽

| ID | 名稱 | 對應設計 | 安全分類 | 程式檔案 |
|----|------|---------|---------|---------|
| SWD-001 | [名稱] | SDD-001 | [A/B/C] | [檔案路徑] |
| SWD-002 | [名稱] | SDD-001 | [A/B/C] | [檔案路徑] |

### 2.2 詳細設計說明

---

#### SWD-001 [函式/類別名稱]

| 屬性 | 內容 |
|-----|------|
| **ID** | SWD-001 |
| **名稱** | [函式/類別名稱] |
| **對應設計** | SDD-001 |
| **對應需求** | SRS-001 |
| **安全分類** | [Class A/B/C] |
| **程式檔案** | [src/module/file.ts] |
| **類型** | [函式/類別/介面] |

**函式簽章**：
```typescript
/**
 * [函式說明]
 * @param param1 - [參數1說明]
 * @param param2 - [參數2說明]
 * @returns [回傳值說明]
 * @throws [例外說明]
 */
function functionName(param1: Type1, param2: Type2): ReturnType
```

**參數說明**：
| 參數 | 類型 | 必填 | 預設值 | 說明 | 有效範圍 |
|-----|------|------|--------|------|---------|
| param1 | Type1 | Y | - | [說明] | [範圍] |
| param2 | Type2 | N | null | [說明] | [範圍] |

**回傳值**：
| 類型 | 說明 | 可能值 |
|-----|------|--------|
| ReturnType | [說明] | [可能值] |

**處理流程**：
```
開始
  │
  ▼
┌─────────────────┐
│ 1. 驗證輸入參數   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 2. 執行業務邏輯   │
└────────┬────────┘
         │
         ▼
    ┌────┴────┐
    │ 是否成功？│
    └────┬────┘
    是 ／ ＼ 否
      ▼     ▼
┌─────┐ ┌─────────┐
│回傳值│ │拋出例外  │
└─────┘ └─────────┘
```

**虛擬碼 (Pseudocode)**：
```
FUNCTION functionName(param1, param2)
    // Step 1: 驗證輸入
    IF param1 is invalid THEN
        THROW InvalidParameterException
    END IF

    // Step 2: 執行業務邏輯
    result = processData(param1)

    // Step 3: 回傳結果
    RETURN result
END FUNCTION
```

**相依性**：
| 相依項目 | 類型 | 說明 |
|---------|------|------|
| SWD-002 | 函式呼叫 | 呼叫 processData 函式 |
| [Library] | 外部程式庫 | 使用 xxx 功能 |

---

#### SWD-002 [函式/類別名稱]

| 屬性 | 內容 |
|-----|------|
| **ID** | SWD-002 |
| **名稱** | [函式/類別名稱] |
| **對應設計** | SDD-001 |
| **對應需求** | SRS-001 |
| **安全分類** | [Class A/B/C] |
| **程式檔案** | [src/module/file.ts] |
| **類型** | [函式/類別/介面] |

**類別定義**：
```typescript
/**
 * [類別說明]
 */
class ClassName {
    // 屬性
    private property1: Type1;
    public property2: Type2;

    // 建構函式
    constructor(param1: Type1) {
        this.property1 = param1;
    }

    // 方法
    public method1(): ReturnType {
        // ...
    }
}
```

**屬性說明**：
| 屬性 | 類型 | 存取修飾 | 說明 |
|-----|------|---------|------|
| property1 | Type1 | private | [說明] |
| property2 | Type2 | public | [說明] |

**方法說明**：
| 方法 | 參數 | 回傳值 | 說明 |
|-----|------|--------|------|
| method1() | - | ReturnType | [說明] |
| method2(p1) | Type1 | void | [說明] |

---

## 3. 演算法說明

### 3.1 演算法總覽

| ID | 名稱 | 使用位置 | 複雜度 |
|----|------|---------|--------|
| ALG-001 | [演算法名稱] | SWD-001 | O(n) |

### 3.2 演算法詳細說明

---

#### ALG-001 [演算法名稱]

| 屬性 | 內容 |
|-----|------|
| **ID** | ALG-001 |
| **名稱** | [演算法名稱] |
| **使用位置** | SWD-001, SWD-003 |
| **時間複雜度** | O(n) |
| **空間複雜度** | O(1) |

**演算法描述**：
[描述演算法的目的和原理]

**虛擬碼**：
```
ALGORITHM algorithmName(input)
    INPUT: [輸入說明]
    OUTPUT: [輸出說明]

    FOR i = 0 TO length(input) - 1
        // Step 1: [步驟說明]
        process(input[i])

        // Step 2: [步驟說明]
        IF condition THEN
            result = compute(input[i])
        END IF
    END FOR

    RETURN result
END ALGORITHM
```

**範例**：
```
輸入: [1, 2, 3, 4, 5]
處理過程:
  i=0: process(1) → result=1
  i=1: process(2) → result=3
  ...
輸出: 15
```

---

## 4. 資料結構定義

### 4.1 資料結構總覽

| ID | 名稱 | 類型 | 使用位置 |
|----|------|------|---------|
| DS-001 | [結構名稱] | Interface | SWD-001 |
| DS-002 | [結構名稱] | Enum | SWD-002 |

### 4.2 資料結構詳細定義

---

#### DS-001 [結構名稱]

| 屬性 | 內容 |
|-----|------|
| **ID** | DS-001 |
| **名稱** | [結構名稱] |
| **類型** | Interface |
| **使用位置** | SWD-001, SWD-002 |

**定義**：
```typescript
interface IDataStructure {
    id: string;           // 唯一識別碼
    name: string;         // 名稱
    value: number;        // 數值
    status: StatusEnum;   // 狀態
    createdAt: Date;      // 建立時間
    metadata?: object;    // 選填的元資料
}
```

**欄位說明**：
| 欄位 | 類型 | 必填 | 說明 | 驗證規則 |
|-----|------|------|------|---------|
| id | string | Y | 唯一識別碼 | UUID 格式 |
| name | string | Y | 名稱 | 1-100 字元 |
| value | number | Y | 數值 | >= 0 |
| status | StatusEnum | Y | 狀態 | 見 DS-002 |
| createdAt | Date | Y | 建立時間 | ISO 8601 |
| metadata | object | N | 元資料 | - |

---

#### DS-002 [列舉名稱]

| 屬性 | 內容 |
|-----|------|
| **ID** | DS-002 |
| **名稱** | StatusEnum |
| **類型** | Enum |
| **使用位置** | DS-001, SWD-001 |

**定義**：
```typescript
enum StatusEnum {
    PENDING = 'PENDING',     // 待處理
    PROCESSING = 'PROCESSING', // 處理中
    COMPLETED = 'COMPLETED',   // 已完成
    FAILED = 'FAILED'         // 失敗
}
```

**值說明**：
| 值 | 說明 | 轉換規則 |
|----|------|---------|
| PENDING | 待處理 | 初始狀態 |
| PROCESSING | 處理中 | 從 PENDING 轉換 |
| COMPLETED | 已完成 | 從 PROCESSING 轉換 |
| FAILED | 失敗 | 從 PROCESSING 轉換 |

---

## 5. 錯誤處理機制

### 5.1 錯誤碼定義

| 錯誤碼 | 名稱 | 說明 | 嚴重程度 |
|--------|------|------|---------|
| E001 | InvalidParameter | 無效的輸入參數 | Warning |
| E002 | DataNotFound | 找不到資料 | Warning |
| E003 | ProcessingError | 處理過程發生錯誤 | Error |
| E004 | SystemFailure | 系統故障 | Critical |

### 5.2 例外處理策略

---

#### 5.2.1 輸入驗證錯誤

| 屬性 | 內容 |
|-----|------|
| **錯誤碼** | E001 |
| **發生位置** | SWD-001, SWD-002 |
| **處理方式** | 回傳錯誤訊息，不中斷系統 |
| **記錄等級** | Warning |

**處理流程**：
```
1. 捕獲 InvalidParameterException
2. 記錄錯誤資訊 (參數名稱、傳入值、預期格式)
3. 回傳標準化錯誤回應
4. 繼續接受後續請求
```

---

#### 5.2.2 系統故障

| 屬性 | 內容 |
|-----|------|
| **錯誤碼** | E004 |
| **發生位置** | 全系統 |
| **處理方式** | 安全關機程序 |
| **記錄等級** | Critical |

**處理流程**：
```
1. 捕獲 SystemFailureException
2. 立即記錄完整錯誤堆疊
3. 儲存目前狀態 (如可能)
4. 發送告警通知
5. 執行安全關機程序
```

### 5.3 錯誤恢復機制

| 錯誤類型 | 恢復策略 | 最大重試次數 | 重試間隔 |
|---------|---------|-------------|---------|
| 網路逾時 | 自動重試 | 3 | 1秒 |
| 資料庫連線 | 重新連線 | 5 | 2秒 |
| 外部服務 | 降級處理 | 2 | 5秒 |

---

## 6. 附錄

### 6.1 程式碼規範

| 項目 | 規範 |
|-----|------|
| 命名慣例 | camelCase (變數), PascalCase (類別) |
| 縮排 | 2 spaces |
| 行寬上限 | 100 字元 |
| 註解語言 | 繁體中文 |

### 6.2 術語定義

| 術語 | 定義 |
|-----|------|
| [術語] | [定義] |

### 6.3 縮寫

| 縮寫 | 全稱 |
|-----|------|
| SWD | Software Detailed Design |
| ALG | Algorithm |
| DS | Data Structure |

---

## 簽核

| 角色 | 姓名 | 簽名 | 日期 |
|-----|------|------|------|
| 作者 | | | |
| 審核者 | | | |
| 核准者 | | | |
