# /docindex Command

文件索引與全文搜尋命令

## 使用方式

```
/docindex <action> [options]
```

## Actions

### index - 索引文件
```bash
/docindex index <目錄路徑> [-m <最大MB>] [-i <索引目錄>]
```

**參數:**
- `<目錄路徑>`: 要索引的目錄 (必填)
- `-m, --max-size`: 最大檔案大小 (MB)，預設 20
- `-i, --index-dir`: 索引儲存目錄，預設 ./index-data

**範例:**
- `/docindex index /Users/jrjohn/Documents/個人`
- `/docindex index /path/to/docs -m 50`
- `/docindex index /path/to/docs -m 10 -i /path/to/index`

### search - 搜尋文件
```bash
/docindex search <關鍵字> [-n <數量>] [-i <索引目錄>]
```

**參數:**
- `<關鍵字>`: 搜尋關鍵字 (必填)
- `-n, --max-results`: 最大結果數，預設 30
- `-i, --index-dir`: 索引目錄，預設 ./index-data

**範例:**
- `/docindex search 妄尽还源观`
- `/docindex search 地藏 -n 10`

### list - 列出已索引文件
```bash
/docindex list [-n <數量>]
```

### stats - 顯示索引統計
```bash
/docindex stats
```

### clear - 清除索引
```bash
/docindex clear [-f]
```

## 執行環境

需要 Java 17:
```bash
export JAVA_HOME=/Users/jrjohn/Library/Java/JavaVirtualMachines/ms-17.0.16/Contents/Home
```

## 工具路徑

```
/Users/jrjohn/Documents/projects/doc_index/doc-indexer/build/libs/doc-indexer-1.0.0-all.jar
```

## 完整命令格式

```bash
export JAVA_HOME=/Users/jrjohn/Library/Java/JavaVirtualMachines/ms-17.0.16/Contents/Home && java -jar /Users/jrjohn/Documents/projects/doc_index/doc-indexer/build/libs/doc-indexer-1.0.0-all.jar <command> [options]
```
