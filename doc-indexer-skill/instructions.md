# Doc Indexer Skill

文件索引與全文搜尋工具。使用 Apache Tika 提取文件內容，Apache Lucene 建立全文索引。

## 平台支援

支援 **macOS**、**Linux** 和 **Windows** 平台。

## 安裝方式

### 首次安裝

根據平台執行對應的安裝腳本：

**macOS / Linux:**
```bash
bash ~/.claude/skills/doc-indexer-skill/setup/setup.sh
```

**Windows (PowerShell):**
```powershell
PowerShell -ExecutionPolicy Bypass -File "$env:USERPROFILE\.claude\skills\doc-indexer-skill\setup\setup.ps1"
```

安裝腳本會自動：
1. 檢查/安裝 Java 17+
2. 下載 doc-indexer JAR
3. 產生設定檔 `config.env`

## 平台偵測與執行命令

### 偵測當前平台

根據環境變數偵測平台：
- **macOS/Linux**: 檢查 `$HOME` 變數
- **Windows**: 檢查 `$env:USERPROFILE` 變數

### macOS 執行命令

```bash
# 讀取設定檔 (如果存在)
CONFIG_FILE="$HOME/.claude/skills/doc-indexer-skill/config.env"
if [ -f "$CONFIG_FILE" ]; then
    source "$CONFIG_FILE"
fi

# 預設值 (向後相容)
JAVA_HOME="${JAVA_HOME:-/Users/jrjohn/Library/Java/JavaVirtualMachines/ms-17.0.16/Contents/Home}"
DOC_INDEXER_JAR="${DOC_INDEXER_JAR:-/Users/jrjohn/Documents/projects/doc_index/doc-indexer/build/libs/doc-indexer-1.0.0-all.jar}"

# 執行命令
export JAVA_HOME && java -jar "$DOC_INDEXER_JAR" <command> [options]
```

**簡化版 (使用預設路徑):**
```bash
export JAVA_HOME=/Users/jrjohn/Library/Java/JavaVirtualMachines/ms-17.0.16/Contents/Home && java -jar /Users/jrjohn/Documents/projects/doc_index/doc-indexer/build/libs/doc-indexer-1.0.0-all.jar <command> [options]
```

### Windows 執行命令

```powershell
# 讀取設定檔
$ConfigFile = "$env:USERPROFILE\.claude\skills\doc-indexer-skill\config.env"
if (Test-Path $ConfigFile) {
    Get-Content $ConfigFile | ForEach-Object {
        if ($_ -match '^([^=]+)=(.*)$') {
            Set-Item -Path "env:$($Matches[1])" -Value $Matches[2]
        }
    }
}

# 執行命令
java -jar "$env:DOC_INDEXER_JAR" <command> [options]
```

**簡化版:**
```powershell
java -jar "$env:LOCALAPPDATA\doc-indexer\doc-indexer-1.0.0-all.jar" <command> [options]
```

## 快速參考

| 命令 | 用途 | 範例 |
|------|------|------|
| `search` | 搜尋文件 | `search "關鍵字"` |
| `index` | 建立索引 | `index /path/to/docs -m 20` |
| `list` | 列出已索引文件 | `list -n 50` |
| `read` | 讀取文件內容 | `read /path/to/file.pdf` |
| `stats` | 索引統計 | `stats` |
| `clear` | 清除索引 | `clear -f` |

## 使用方式

### 1. 搜尋文件

當用戶詢問「找文件」、「搜尋」、「哪個文件有提到...」時：

**macOS/Linux:**
```bash
export JAVA_HOME=/Users/jrjohn/Library/Java/JavaVirtualMachines/ms-17.0.16/Contents/Home && java -jar /Users/jrjohn/Documents/projects/doc_index/doc-indexer/build/libs/doc-indexer-1.0.0-all.jar search "搜尋關鍵字" -n 5
```

**Windows:**
```powershell
java -jar "$env:LOCALAPPDATA\doc-indexer\doc-indexer-1.0.0-all.jar" search "搜尋關鍵字" -n 5
```

**參數：**
- `"搜尋關鍵字"`: 支援中英文
- `-n 5`: 最多返回筆數 (預設 5，避免輸出被摺疊)
- `-s, --min-score`: 最低分數閾值 (預設 1.0，過濾低相關度結果)
- `--json`: JSON 輸出

**提示：**
- 按 `ctrl+o` 可展開查看完整輸出
- 使用 `-n 10`、`-n 20` 可增加結果數量
- 使用 `-s 0` 可關閉分數過濾，顯示所有結果

**搜尋語法：**
- 簡單：`"報告"`
- 多詞：`"專案 進度"`
- 精確：`"\"年度報告\""`
- 萬用：`"報告*"`
- 布林：`"報告 AND 2024"`

### 2. 建立索引

當用戶說「索引資料夾」、「加入索引」時：

**macOS/Linux:**
```bash
export JAVA_HOME=/Users/jrjohn/Library/Java/JavaVirtualMachines/ms-17.0.16/Contents/Home && java -jar /Users/jrjohn/Documents/projects/doc_index/doc-indexer/build/libs/doc-indexer-1.0.0-all.jar index "/path/to/documents" -m 20
```

**Windows:**
```powershell
java -jar "$env:LOCALAPPDATA\doc-indexer\doc-indexer-1.0.0-all.jar" index "C:\path\to\documents" -m 20
```

**參數：**
- `-m, --max-size`: 最大檔案大小 MB (預設 20)
- `-i, --index-dir`: 索引儲存位置 (預設 ./index-data)
- `-r, --recursive`: 遞迴子目錄 (預設 true)
- `--json`: JSON 輸出

**支援格式：**
- 文件：PDF, DOC/DOCX, XLS/XLSX, PPT/PPTX, ODT, RTF
- 文字：TXT, MD, JSON, XML, YAML, HTML, CSV
- 程式碼：Java, Python, JS, TS, Go, Rust 等
- 圖片 (OCR)：PNG, JPG, JPEG, GIF, BMP, TIFF, WebP
- 壓縮檔：ZIP, TAR, GZ, 7Z, RAR

### 3. 列出已索引文件

**macOS/Linux:**
```bash
export JAVA_HOME=/Users/jrjohn/Library/Java/JavaVirtualMachines/ms-17.0.16/Contents/Home && java -jar /Users/jrjohn/Documents/projects/doc_index/doc-indexer/build/libs/doc-indexer-1.0.0-all.jar list -n 50
```

**Windows:**
```powershell
java -jar "$env:LOCALAPPDATA\doc-indexer\doc-indexer-1.0.0-all.jar" list -n 50
```

### 4. 讀取文件內容

**macOS/Linux:**
```bash
export JAVA_HOME=/Users/jrjohn/Library/Java/JavaVirtualMachines/ms-17.0.16/Contents/Home && java -jar /Users/jrjohn/Documents/projects/doc_index/doc-indexer/build/libs/doc-indexer-1.0.0-all.jar read "/path/to/file.pdf" -l 5000
```

**Windows:**
```powershell
java -jar "$env:LOCALAPPDATA\doc-indexer\doc-indexer-1.0.0-all.jar" read "C:\path\to\file.pdf" -l 5000
```

### 5. 查看統計

**macOS/Linux:**
```bash
export JAVA_HOME=/Users/jrjohn/Library/Java/JavaVirtualMachines/ms-17.0.16/Contents/Home && java -jar /Users/jrjohn/Documents/projects/doc_index/doc-indexer/build/libs/doc-indexer-1.0.0-all.jar stats
```

**Windows:**
```powershell
java -jar "$env:LOCALAPPDATA\doc-indexer\doc-indexer-1.0.0-all.jar" stats
```

### 6. 清除索引

**macOS/Linux:**
```bash
export JAVA_HOME=/Users/jrjohn/Library/Java/JavaVirtualMachines/ms-17.0.16/Contents/Home && java -jar /Users/jrjohn/Documents/projects/doc_index/doc-indexer/build/libs/doc-indexer-1.0.0-all.jar clear -f
```

**Windows:**
```powershell
java -jar "$env:LOCALAPPDATA\doc-indexer\doc-indexer-1.0.0-all.jar" clear -f
```

## 搜尋結果輸出格式

標準輸出：
```
搜尋: 關鍵字
索引檔: /path/to/index-data

搜尋到 N 筆文件

序號 1
文件唯一識別碼: abc123
完整檔案路徑: /path/to/file.pdf
檔案名稱: file.pdf
MIME 類型: application/pdf
搜尋相關度分數: 5.2340
上下文摘要: ...匹配片段...
檔案大小 (KBytes): 123.4
最後修改時間: 2025-12-04 15:48
索引時間: 2026-01-20 15:06
總頁數: 10
匹配的頁碼陣列: [1, 3, 5]
```

## 功能特點

- **跨平台**: 支援 macOS, Linux, Windows
- **中文分詞**: SmartChineseAnalyzer
- **OCR 支援**: Tesseract (繁中/簡中/英文)
- **分頁索引**: PDF 分頁提取，顯示匹配頁碼
- **關鍵字高亮**: 紅色標示關鍵字
- **欄位權重**: 檔名 3x, 內容 1x, 元數據 1.5x

## 原始碼與自訂建置

原始碼包含在 `~/.claude/skills/doc-indexer-skill/source/` 目錄內，使用者可自行修改並建置。

### 目錄結構

```
source/
├── src/main/java/com/docindex/
│   ├── cli/DocIndexCli.java      # CLI 主程式
│   ├── core/LuceneIndexer.java   # Lucene 索引服務
│   ├── core/TikaExtractor.java   # Tika 文件提取
│   └── model/                    # 資料模型
├── build.gradle                  # Gradle 建置設定
├── gradlew                       # macOS/Linux 建置腳本
└── gradlew.bat                   # Windows 建置腳本
```

### 從原始碼建置

**macOS/Linux:**
```bash
cd ~/.claude/skills/doc-indexer-skill/source
chmod +x gradlew
./gradlew shadowJar --no-daemon
# 產出: build/libs/doc-indexer-1.0.0-all.jar
```

**Windows:**
```powershell
cd "$env:USERPROFILE\.claude\skills\doc-indexer-skill\source"
.\gradlew.bat shadowJar --no-daemon
# 產出: build\libs\doc-indexer-1.0.0-all.jar
```

### 常見修改

| 修改項目 | 檔案位置 |
|---------|---------|
| 新增 CLI 命令 | `cli/DocIndexCli.java` |
| 調整搜尋權重 | `core/LuceneIndexer.java` |
| 支援新檔案格式 | `core/TikaExtractor.java` |
| 變更輸出格式 | `cli/DocIndexCli.java` |

### 建置後使用

建置完成後，更新 `config.env` 指向新的 JAR：

```bash
# macOS/Linux
echo 'DOC_INDEXER_JAR="$HOME/.claude/skills/doc-indexer-skill/source/build/libs/doc-indexer-1.0.0-all.jar"' >> ~/.claude/skills/doc-indexer-skill/config.env
```

```powershell
# Windows
Add-Content "$env:USERPROFILE\.claude\skills\doc-indexer-skill\config.env" 'DOC_INDEXER_JAR="$env:USERPROFILE\.claude\skills\doc-indexer-skill\source\build\libs\doc-indexer-1.0.0-all.jar"'
```

## Claude CLI 輸出規範

執行搜尋後，**只呈現工具的標準格式輸出**：
- 不要加表格摘要
- 不要加「主要結果包含」等額外分析
- 完整列出所有結果，不要用 `...` 省略
- 直接呈現工具輸出的標準格式即可
- 預設使用 `-n 5` 限制結果數量，避免輸出過長被 CLI 摺疊
- 執行後提醒用戶：「按 `ctrl+o` 可展開查看完整輸出」

## 注意事項

1. **首次使用**: 請先執行安裝腳本
2. **索引更新**: 文件變更後需重新執行 index
3. **最大檔案**: 預設跳過超過 20MB 的檔案，可用 -m 調整
4. **索引位置**: 預設 `./index-data`
5. **Java 版本**: 需要 Java 17 或更高版本
