---
name: doc-indexer
description: 文件索引與全文搜尋工具。使用 /doc-indexer search "關鍵字" 搜尋文件，/doc-indexer index "目錄" 建立索引。支援 PDF, Word, Excel, 圖片 OCR，中文分詞，分頁索引。
allowed-tools: [Bash, Read, Write]
---

# Doc Indexer Skill

文件索引與全文搜尋工具，使用 Apache Tika 提取文件內容，Apache Lucene 建立全文索引。

## 執行命令

使用以下命令執行 doc-indexer：

```bash
export JAVA_HOME=/Users/jrjohn/Library/Java/JavaVirtualMachines/ms-17.0.16/Contents/Home && java -jar /Users/jrjohn/Documents/projects/doc_index/doc-indexer/build/libs/doc-indexer-1.0.0-all.jar <command> [options]
```

**可用命令:** `index`, `search`, `list`, `stats`, `read`, `clear`

## 功能特點

- **多格式支援**: PDF, Word, Excel, PowerPoint, 純文字, 程式碼, 圖片 (OCR)
- **中文分詞**: 使用 SmartChineseAnalyzer 進行中文分詞
- **OCR 支援**: 支援圖片文字辨識 (繁體中文、簡體中文、英文)
- **分頁索引**: PDF 文件支援分頁內容提取，搜尋時顯示匹配頁碼
- **關鍵字高亮**: 搜尋結果中關鍵字以紅色高亮顯示

## 工具位置

```
/Users/jrjohn/Documents/projects/doc_index/doc-indexer/build/libs/doc-indexer-1.0.0-all.jar
```

## 使用前準備

需要使用 Java 17 執行：
```bash
export JAVA_HOME=/Users/jrjohn/Library/Java/JavaVirtualMachines/ms-17.0.16/Contents/Home
```

## 命令說明

### 1. 索引文件 (index)

```bash
java -jar doc-indexer-1.0.0-all.jar index <目錄或檔案路徑> [選項]
```

**參數:**
| 參數 | 說明 | 預設值 |
|------|------|--------|
| `<path>` | 要索引的目錄或檔案路徑 | (必填) |
| `-i, --index-dir` | 索引儲存目錄 | `./index-data` |
| `-m, --max-size` | 最大檔案大小 (MB)，超過則跳過 | `20` |
| `-r, --recursive` | 是否遞迴處理子目錄 | `true` |
| `--json` | 以 JSON 格式輸出 | `false` |

**範例:**
```bash
# 索引指定目錄 (預設最大 20MB)
java -jar doc-indexer-1.0.0-all.jar index "/Users/jrjohn/Documents/個人"

# 指定索引儲存位置
java -jar doc-indexer-1.0.0-all.jar index "/path/to/docs" -i "/path/to/index"

# 設定最大檔案大小為 50MB
java -jar doc-indexer-1.0.0-all.jar index "/path/to/docs" -m 50

# 設定最大檔案大小為 10MB，並指定索引位置
java -jar doc-indexer-1.0.0-all.jar index "/path/to/docs" -m 10 -i "/path/to/index"
```

### 2. 搜尋文件 (search)

```bash
java -jar doc-indexer-1.0.0-all.jar search <關鍵字> [選項]
```

**參數:**
| 參數 | 說明 | 預設值 |
|------|------|--------|
| `<query>` | 搜尋關鍵字 | (必填) |
| `-i, --index-dir` | 索引目錄 | `./index-data` |
| `-n, --max-results` | 最大結果數量 | `30` |
| `--json` | 以 JSON 格式輸出 | `false` |

**輸出欄位:**
- 序號
- 文件唯一識別碼
- 完整檔案路徑
- 檔案名稱 (關鍵字高亮)
- MIME 類型
- 搜尋相關度分數
- 上下文摘要 (關鍵字高亮)
- 檔案大小 (KBytes)
- 最後修改時間
- 索引時間
- 總頁數
- 匹配的頁碼陣列

**範例:**
```bash
# 搜尋關鍵字
java -jar doc-indexer-1.0.0-all.jar search "妄尽还源观"

# 限制結果數量
java -jar doc-indexer-1.0.0-all.jar search "地藏" -n 10

# JSON 輸出
java -jar doc-indexer-1.0.0-all.jar search "佛經" --json
```

### 3. 列出文件 (list)

```bash
java -jar doc-indexer-1.0.0-all.jar list [選項]
```

**參數:**
| 參數 | 說明 | 預設值 |
|------|------|--------|
| `-i, --index-dir` | 索引目錄 | `./index-data` |
| `-n, --max-results` | 最大結果數量 | `100` |
| `--json` | 以 JSON 格式輸出 | `false` |

### 4. 索引統計 (stats)

```bash
java -jar doc-indexer-1.0.0-all.jar stats [選項]
```

**輸出:**
- 索引路徑
- 總文件數
- 已刪除文件數

### 5. 讀取檔案 (read)

```bash
java -jar doc-indexer-1.0.0-all.jar read <檔案路徑> [選項]
```

**參數:**
| 參數 | 說明 | 預設值 |
|------|------|--------|
| `<path>` | 檔案路徑 | (必填) |
| `-l, --limit` | 內容長度限制 | `5000` |
| `--json` | 以 JSON 格式輸出 | `false` |

### 6. 清除索引 (clear)

```bash
java -jar doc-indexer-1.0.0-all.jar clear [選項]
```

**參數:**
| 參數 | 說明 | 預設值 |
|------|------|--------|
| `-i, --index-dir` | 索引目錄 | `./index-data` |
| `-f, --force` | 強制清除 (不確認) | `false` |

## 支援的檔案格式

### 文件類型
- PDF (`pdf`)
- Microsoft Word (`doc`, `docx`)
- Microsoft Excel (`xls`, `xlsx`)
- Microsoft PowerPoint (`ppt`, `pptx`)
- OpenDocument (`odt`, `ods`, `odp`)
- RTF (`rtf`)

### 文字類型
- 純文字 (`txt`, `md`, `markdown`)
- JSON (`json`)
- XML (`xml`)
- YAML (`yaml`, `yml`)
- HTML (`html`, `htm`)
- CSV/TSV (`csv`, `tsv`)

### 程式碼
- Java, Python, JavaScript, TypeScript
- C, C++, C#, Go, Rust, Ruby, PHP
- Swift, Kotlin, SQL, Shell scripts

### 圖片 (OCR)
- PNG, JPG, JPEG, GIF, BMP, TIFF, WebP

### 壓縮檔
- ZIP, TAR, GZ, 7Z, RAR

## 搜尋語法

支援 Lucene 查詢語法：

| 語法 | 說明 | 範例 |
|------|------|------|
| 單詞 | 搜尋單一關鍵字 | `佛經` |
| 詞組 | 用引號包圍搜尋詞組 | `"心經"` |
| AND | 同時包含 | `佛經 AND 般若` |
| OR | 任一包含 | `心經 OR 金剛經` |
| NOT | 排除 | `佛經 NOT 阿彌陀` |
| 萬用字元 | * 多字元, ? 單字元 | `佛*` |
| 欄位搜尋 | 指定欄位 | `fileName:心經` |

## 權重設定

搜尋時欄位權重：
- 檔案名稱 (fileName): 3.0x
- 內容 (content): 1.0x
- 元數據 (metadata): 1.5x

## 技術架構

- **Apache Tika 2.9.1**: 文件內容提取
- **Apache Lucene 9.9.1**: 全文索引與搜尋
- **PDFBox**: PDF 分頁內容提取
- **Tesseract OCR**: 圖片文字辨識
- **SmartChineseAnalyzer**: 中文分詞
- **picocli**: CLI 命令解析

## 專案位置

```
/Users/jrjohn/Documents/projects/doc_index/doc-indexer/
```

## 建置命令

```bash
cd /Users/jrjohn/Documents/projects/doc_index/doc-indexer
export JAVA_HOME=/Users/jrjohn/Library/Java/JavaVirtualMachines/ms-17.0.16/Contents/Home
./gradlew shadowJar --no-daemon
```
