# Doc Indexer Skill

文件索引與全文搜尋工具 - 使用 Apache Tika + Apache Lucene

## 快速開始

### 索引文件
```bash
java -jar doc-indexer-1.0.0-all.jar index "/path/to/documents" [-m 最大MB]
```

### 搜尋文件
```bash
java -jar doc-indexer-1.0.0-all.jar search "關鍵字" [-n 數量]
```

## 功能特點

| 功能 | 說明 |
|------|------|
| 多格式支援 | PDF, Word, Excel, PPT, 純文字, 程式碼 |
| OCR 支援 | PNG, JPG, TIFF 等圖片文字辨識 |
| 中文分詞 | SmartChineseAnalyzer |
| 分頁索引 | PDF 分頁提取，顯示匹配頁碼 |
| 關鍵字高亮 | 搜尋結果紅色標示關鍵字 |

## 命令列表

| 命令 | 說明 |
|------|------|
| `index` | 索引文件 |
| `search` | 搜尋文件 |
| `list` | 列出已索引文件 |
| `stats` | 顯示索引統計 |
| `read` | 讀取檔案內容 |
| `clear` | 清除索引 |

## 索引參數

| 參數 | 說明 | 預設值 |
|------|------|--------|
| `<path>` | 索引目錄或檔案 | (必填) |
| `-i, --index-dir` | 索引儲存位置 | `./index-data` |
| `-m, --max-size` | 最大檔案大小 (MB) | `20` |
| `-r, --recursive` | 遞迴子目錄 | `true` |
| `--json` | JSON 輸出 | `false` |

## 搜尋參數

| 參數 | 說明 | 預設值 |
|------|------|--------|
| `<query>` | 搜尋關鍵字 | (必填) |
| `-i, --index-dir` | 索引目錄 | `./index-data` |
| `-n, --max-results` | 最大結果數 | `30` |
| `--json` | JSON 輸出 | `false` |

## 搜尋結果欄位

- 序號
- 文件唯一識別碼
- 完整檔案路徑
- 檔案名稱
- MIME 類型
- 搜尋相關度分數
- 上下文摘要
- 檔案大小 (KBytes)
- 最後修改時間
- 索引時間
- 總頁數
- 匹配的頁碼陣列

## 使用環境

```bash
export JAVA_HOME=/Users/jrjohn/Library/Java/JavaVirtualMachines/ms-17.0.16/Contents/Home
```

## 工具位置

```
/Users/jrjohn/Documents/projects/doc_index/doc-indexer/build/libs/doc-indexer-1.0.0-all.jar
```
