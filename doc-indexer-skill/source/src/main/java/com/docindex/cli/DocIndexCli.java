package com.docindex.cli;

import com.docindex.core.LuceneIndexer;
import com.docindex.core.TikaExtractor;
import com.docindex.model.DocumentInfo;
import com.docindex.model.SearchResult;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import picocli.CommandLine;
import picocli.CommandLine.Command;
import picocli.CommandLine.Option;
import picocli.CommandLine.Parameters;

import java.io.IOException;
import java.nio.file.*;
import java.nio.file.attribute.BasicFileAttributes;
import java.time.Instant;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.concurrent.Callable;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * 文件索引 CLI 工具
 */
@Command(
    name = "docindex",
    mixinStandardHelpOptions = true,
    version = "1.0.0",
    description = "Document indexing and search tool using Tika and Lucene",
    subcommands = {
        DocIndexCli.IndexCommand.class,
        DocIndexCli.SearchCommand.class,
        DocIndexCli.ListCommand.class,
        DocIndexCli.StatsCommand.class,
        DocIndexCli.ReadCommand.class,
        DocIndexCli.ClearCommand.class
    }
)
public class DocIndexCli implements Callable<Integer> {

    private static final Gson gson = new GsonBuilder().setPrettyPrinting().create();

    // ANSI 顏色碼
    private static final String ANSI_RESET = "\u001B[0m";
    private static final String ANSI_RED = "\u001B[91m";      // 亮紅色
    private static final String ANSI_GREEN = "\u001B[92m";    // 亮綠色
    private static final String ANSI_YELLOW = "\u001B[93m";   // 亮黃色
    private static final String ANSI_BLUE = "\u001B[94m";     // 亮藍色
    private static final String ANSI_CYAN = "\u001B[96m";     // 亮青色
    private static final String ANSI_BOLD = "\u001B[1m";      // 粗體
    private static final String ANSI_DIM = "\u001B[2m";       // 暗淡
    private static final String ANSI_RED_BOLD = "\u001B[1;91m"; // 亮紅色+粗體 (組合序列)
    // 256色模式的紅色 (更好的終端機相容性)
    private static final String ANSI_RED_256 = "\u001B[38;5;196m";  // 256色亮紅
    // 反白模式 (反轉前景/背景色，最可靠的高亮方式)
    private static final String ANSI_REVERSE = "\u001B[7m";         // 反白

    // 日期格式
    private static final DateTimeFormatter DATE_FORMAT = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm")
            .withZone(ZoneId.systemDefault());

    /**
     * 格式化日期字串
     */
    private static String formatDate(String isoDate) {
        if (isoDate == null || isoDate.isEmpty()) return "-";
        try {
            Instant instant = Instant.parse(isoDate);
            return DATE_FORMAT.format(instant);
        } catch (Exception e) {
            return isoDate;
        }
    }

    /**
     * 高亮關鍵字（使用反白+紅色，確保在中文字串中也能正確顯示）
     */
    private static String highlightKeywords(String text, String query) {
        if (text == null || text.isEmpty() || query == null || query.isEmpty()) {
            return text;
        }

        String result = text;
        String[] terms = query.split("\\s+");  // 不轉換大小寫，保留原始查詢
        for (String term : terms) {
            String cleanTerm = term.replaceAll("[^\\p{L}\\p{N}]", "");
            if (cleanTerm.isEmpty()) continue;

            // 使用反白+紅色組合（在中文字串中更可靠）
            Pattern pattern = Pattern.compile("(" + Pattern.quote(cleanTerm) + ")", Pattern.CASE_INSENSITIVE | Pattern.UNICODE_CASE);
            Matcher matcher = pattern.matcher(result);
            result = matcher.replaceAll(ANSI_REVERSE + ANSI_RED + "$1" + ANSI_RESET);
        }
        return result;
    }

    /**
     * 計算字串顯示寬度（中文字算2，英文算1）
     */
    private static int displayWidth(String str) {
        if (str == null) return 0;
        int width = 0;
        for (char c : str.toCharArray()) {
            if (c >= 0x4E00 && c <= 0x9FFF || c >= 0x3000 && c <= 0x303F ||
                c >= 0xFF00 && c <= 0xFFEF) {
                width += 2;  // 中文字元
            } else {
                width += 1;  // 英文字元
            }
        }
        return width;
    }

    /**
     * 填充字串到指定顯示寬度
     */
    private static String padToWidth(String str, int targetWidth) {
        int currentWidth = displayWidth(str);
        if (currentWidth >= targetWidth) {
            return str;
        }
        return str + " ".repeat(targetWidth - currentWidth);
    }

    /**
     * 截斷字串到指定顯示寬度
     */
    private static String truncateToWidth(String str, int maxWidth) {
        if (str == null) return "";
        int width = 0;
        StringBuilder sb = new StringBuilder();
        for (char c : str.toCharArray()) {
            int charWidth = (c >= 0x4E00 && c <= 0x9FFF || c >= 0x3000 && c <= 0x303F ||
                            c >= 0xFF00 && c <= 0xFFEF) ? 2 : 1;
            if (width + charWidth > maxWidth - 2) {
                sb.append("..");
                break;
            }
            sb.append(c);
            width += charWidth;
        }
        return sb.toString();
    }

    /**
     * 輸出搜尋結果
     */
    private static void printSearchResultsTable(List<SearchResult> results, String query, String indexDir) {
        System.out.println("搜尋: " + ANSI_RED + ANSI_BOLD + query + ANSI_RESET);
        System.out.println("索引檔: " + indexDir);
        System.out.println();
        System.out.println("搜尋到 " + ANSI_CYAN + results.size() + ANSI_RESET + " 筆文件");
        System.out.println();

        if (results.isEmpty()) {
            return;
        }

        for (int i = 0; i < results.size(); i++) {
            SearchResult r = results.get(i);

            System.out.println(ANSI_BOLD + ANSI_CYAN + "序號 " + (i + 1) + ANSI_RESET);
            System.out.println("文件唯一識別碼: " + r.getDocumentId());
            System.out.println("完整檔案路徑: " + r.getFilePath());
            System.out.println("檔案名稱: " + highlightKeywords(r.getFileName(), query));
            System.out.println("MIME 類型: " + (r.getContentType() != null ? r.getContentType() : "-"));
            System.out.println("搜尋相關度分數: " + ANSI_YELLOW + String.format("%.4f", r.getScore()) + ANSI_RESET);

            if (r.getSnippet() != null && !r.getSnippet().isEmpty()) {
                System.out.println("上下文摘要: " + highlightKeywords(r.getSnippet(), query));
            } else {
                System.out.println("上下文摘要: -");
            }

            // 檔案大小轉換為 KB
            double sizeKB = r.getFileSize() / 1024.0;
            System.out.println("檔案大小 (KBytes): " + ANSI_GREEN + String.format("%.1f", sizeKB) + ANSI_RESET);
            System.out.println("最後修改時間: " + formatDate(r.getLastModified()));
            System.out.println("索引時間: " + formatDate(r.getIndexedAt()));
            System.out.println("總頁數: " + (r.getPageCount() > 0 ? r.getPageCount() : "-"));

            if (r.getMatchedPages() != null && !r.getMatchedPages().isEmpty()) {
                System.out.println("匹配的頁碼陣列: " + ANSI_RED + r.getMatchedPages() + ANSI_RESET);
            } else {
                System.out.println("匹配的頁碼陣列: -");
            }

            System.out.println();
        }
    }

    @Option(names = {"-i", "--index-dir"}, description = "Index directory path", defaultValue = "./index-data")
    protected String indexDir;

    @Override
    public Integer call() {
        CommandLine.usage(this, System.out);
        return 0;
    }

    public static void main(String[] args) {
        int exitCode = new CommandLine(new DocIndexCli()).execute(args);
        System.exit(exitCode);
    }

    // ========== 索引命令 ==========
    @Command(name = "index", description = "Index documents from a directory or file")
    static class IndexCommand implements Callable<Integer> {

        @Parameters(index = "0", description = "Path to file or directory to index")
        private String sourcePath;

        @Option(names = {"-i", "--index-dir"}, description = "Index directory path", defaultValue = "./index-data")
        private String indexDir;

        @Option(names = {"-r", "--recursive"}, description = "Recursively index subdirectories", defaultValue = "true")
        private boolean recursive;

        @Option(names = {"--json"}, description = "Output as JSON")
        private boolean jsonOutput;

        @Option(names = {"-m", "--max-size"}, description = "Maximum file size in MB to index (skip larger files)", defaultValue = "20")
        private int maxSizeMB;

        private static final int PROGRESS_BAR_WIDTH = 30;

        @Override
        public Integer call() {
            try {
                Path source = Paths.get(sourcePath).toAbsolutePath();
                Path indexPath = Paths.get(indexDir).toAbsolutePath();
                long maxFileSize = maxSizeMB * 1024L * 1024L;

                // 確保索引目錄存在
                Files.createDirectories(indexPath);

                TikaExtractor extractor = new TikaExtractor();

                // 第一階段：掃描並計算檔案總數
                if (!jsonOutput) {
                    System.out.println("索引目錄: " + source);
                    System.out.println("索引檔: " + indexPath);
                    System.out.println("最大檔案: " + maxSizeMB + " MB");
                    System.out.println();
                    System.out.println("掃描檔案中...");
                }
                List<Path> filesToIndex = new ArrayList<>();
                if (Files.isDirectory(source)) {
                    collectFilePaths(source, extractor, filesToIndex, recursive, maxFileSize);
                } else if (Files.isRegularFile(source)) {
                    if (extractor.isSupported(source)) {
                        filesToIndex.add(source);
                    }
                } else {
                    System.err.println("Path does not exist: " + sourcePath);
                    return 1;
                }

                int totalFiles = filesToIndex.size();
                if (!jsonOutput) {
                    System.out.println("找到 " + totalFiles + " 個檔案\n");
                }

                // 第二階段：索引文件並顯示進度
                int indexedCount = 0;
                int errorCount = 0;
                String currentDir = "";

                try (LuceneIndexer indexer = new LuceneIndexer(indexPath)) {
                    indexer.openWriter();

                    for (int i = 0; i < filesToIndex.size(); i++) {
                        Path file = filesToIndex.get(i);
                        String fileDir = file.getParent().toString();

                        // 更新目錄顯示
                        if (!jsonOutput && !fileDir.equals(currentDir)) {
                            currentDir = fileDir;
                            // 清除進度條那行，顯示目錄
                            System.out.print("\r\033[K");
                            String displayDir = truncatePath(currentDir, 60);
                            System.out.println("📁 " + displayDir);
                        }

                        try {
                            DocumentInfo doc = extractor.extract(file);
                            indexer.indexDocument(doc);
                            indexedCount++;
                        } catch (Exception e) {
                            errorCount++;
                        }

                        // 更新進度條
                        if (!jsonOutput) {
                            printProgress(i + 1, totalFiles, file.getFileName().toString());
                        }
                    }

                    indexer.commit();

                    // 完成後清除進度條
                    if (!jsonOutput) {
                        System.out.print("\r\033[K");
                        System.out.println("\n✅ 索引完成！");
                    }
                }

                Map<String, Object> result = new LinkedHashMap<>();
                result.put("status", "success");
                result.put("indexedCount", indexedCount);
                result.put("totalFiles", totalFiles);
                result.put("errorCount", errorCount);
                result.put("indexPath", indexPath.toString());

                if (jsonOutput) {
                    System.out.println(gson.toJson(result));
                } else {
                    System.out.println("成功索引: " + indexedCount + " 個檔案");
                    if (errorCount > 0) {
                        System.out.println("失敗: " + errorCount + " 個檔案");
                    }
                    System.out.println("索引路徑: " + indexPath);
                }

                return 0;
            } catch (Exception e) {
                System.err.println("Error: " + e.getMessage());
                e.printStackTrace();
                return 1;
            }
        }

        private void printProgress(int current, int total, String fileName) {
            double progress = (double) current / total;
            int percent = (int) (progress * 100);
            int filled = (int) (progress * PROGRESS_BAR_WIDTH);
            int empty = PROGRESS_BAR_WIDTH - filled;

            StringBuilder bar = new StringBuilder();
            // 清除整行並移到行首
            bar.append("\r\033[K");
            bar.append(String.format("%3d%% ", percent));
            for (int i = 0; i < filled; i++) bar.append("█");
            for (int i = 0; i < empty; i++) bar.append("░");
            bar.append(String.format(" [%d/%d] ", current, total));

            // 截斷檔名以適應終端寬度
            String displayName = truncateString(fileName, 25);
            bar.append(displayName);

            // 填充空白確保覆蓋舊內容
            int padding = 80 - bar.length();
            for (int i = 0; i < padding && i < 20; i++) bar.append(" ");

            System.out.print(bar.toString());
            System.out.flush();
        }

        private String truncateString(String str, int maxLen) {
            if (str.length() <= maxLen) return str;
            return str.substring(0, maxLen - 3) + "...";
        }

        private String truncatePath(String path, int maxLen) {
            if (path.length() <= maxLen) return path;
            // 從路徑開頭截斷，保留結尾
            return "..." + path.substring(path.length() - maxLen + 3);
        }

        private void collectFilePaths(Path dir, TikaExtractor extractor, List<Path> files, boolean recursive, long maxFileSize) throws IOException {
            int maxDepth = recursive ? Integer.MAX_VALUE : 1;

            Files.walkFileTree(dir, EnumSet.noneOf(FileVisitOption.class), maxDepth, new SimpleFileVisitor<>() {
                @Override
                public FileVisitResult visitFile(Path file, BasicFileAttributes attrs) {
                    // 跳過超大檔案
                    if (attrs.size() > maxFileSize) {
                        return FileVisitResult.CONTINUE;
                    }
                    if (extractor.isSupported(file)) {
                        files.add(file);
                    }
                    return FileVisitResult.CONTINUE;
                }

                @Override
                public FileVisitResult visitFileFailed(Path file, IOException exc) {
                    return FileVisitResult.CONTINUE;
                }
            });
        }
    }

    // ========== 搜尋命令 ==========
    @Command(name = "search", description = "Search indexed documents")
    static class SearchCommand implements Callable<Integer> {

        // 上下文摘要長度
        private static final int CONTEXT_LENGTH = 300;
        // 讀取檔案內容的最大長度（用於產生摘要）
        private static final int MAX_READ_LENGTH = 500000;  // 500KB

        @Parameters(index = "0", description = "Search query")
        private String query;

        @Option(names = {"-i", "--index-dir"}, description = "Index directory path", defaultValue = "./index-data")
        private String indexDir;

        @Option(names = {"-n", "--max-results"}, description = "Maximum number of results", defaultValue = "30")
        private int maxResults;

        @Option(names = {"-s", "--min-score"}, description = "Minimum score threshold (filter out low-relevance results)", defaultValue = "1.0")
        private double minScore;

        @Option(names = {"--json"}, description = "Output as JSON")
        private boolean jsonOutput;

        @Override
        public Integer call() {
            try {
                Path indexPath = Paths.get(indexDir).toAbsolutePath();

                if (!Files.exists(indexPath)) {
                    System.err.println("Index directory does not exist: " + indexDir);
                    return 1;
                }

                try (LuceneIndexer indexer = new LuceneIndexer(indexPath)) {
                    List<SearchResult> results = indexer.search(query, maxResults);

                    // 過濾低於最低分數閾值的結果
                    if (minScore > 0) {
                        results = results.stream()
                            .filter(r -> r.getScore() >= minScore)
                            .collect(java.util.stream.Collectors.toList());
                    }

                    // 方案 C: 從原始檔案產生摘要
                    TikaExtractor extractor = new TikaExtractor(MAX_READ_LENGTH);
                    for (SearchResult result : results) {
                        String snippet = generateSnippetFromFile(extractor, result.getFilePath(), query);
                        result.setSnippet(snippet);
                    }

                    if (jsonOutput) {
                        Map<String, Object> output = new LinkedHashMap<>();
                        output.put("query", query);
                        output.put("minScore", minScore);
                        output.put("totalResults", results.size());
                        output.put("results", results);
                        System.out.println(gson.toJson(output));
                    } else {
                        // 表格輸出
                        printSearchResultsTable(results, query, indexPath.toString());
                    }
                }

                return 0;
            } catch (Exception e) {
                System.err.println("Error: " + e.getMessage());
                return 1;
            }
        }

        /**
         * 從原始檔案產生上下文摘要
         */
        private String generateSnippetFromFile(TikaExtractor extractor, String filePath, String query) {
            try {
                Path path = Paths.get(filePath);
                if (!Files.exists(path)) {
                    return "(檔案不存在)";
                }

                DocumentInfo doc = extractor.extract(path);
                String content = doc.getContent();
                if (content == null || content.isEmpty()) {
                    return "";
                }

                return createSnippet(content, query, CONTEXT_LENGTH);
            } catch (Exception e) {
                return "(無法讀取檔案)";
            }
        }

        /**
         * 產生搜尋結果摘要
         */
        private String createSnippet(String content, String query, int maxLength) {
            if (content == null || content.isEmpty()) {
                return "";
            }

            // 簡化查詢詞
            String[] queryTerms = query.toLowerCase().split("\\s+");
            String lowerContent = content.toLowerCase();

            // 找到第一個匹配的位置
            int matchPos = -1;
            for (String term : queryTerms) {
                String cleanTerm = term.replaceAll("[^\\p{L}\\p{N}]", "");
                if (!cleanTerm.isEmpty()) {
                    int pos = lowerContent.indexOf(cleanTerm);
                    if (pos != -1 && (matchPos == -1 || pos < matchPos)) {
                        matchPos = pos;
                    }
                }
            }

            // 從匹配位置前後擷取摘要
            int start = matchPos > 0 ? Math.max(0, matchPos - 50) : 0;
            int end = Math.min(content.length(), start + maxLength);

            String snippet = content.substring(start, end).trim();

            // 加上省略號
            if (start > 0) snippet = "..." + snippet;
            if (end < content.length()) snippet = snippet + "...";

            return snippet.replaceAll("\\s+", " ");
        }
    }

    // ========== 列出命令 ==========
    @Command(name = "list", description = "List all indexed documents")
    static class ListCommand implements Callable<Integer> {

        @Option(names = {"-i", "--index-dir"}, description = "Index directory path", defaultValue = "./index-data")
        private String indexDir;

        @Option(names = {"-n", "--max-results"}, description = "Maximum number of results", defaultValue = "100")
        private int maxResults;

        @Option(names = {"--json"}, description = "Output as JSON")
        private boolean jsonOutput;

        @Override
        public Integer call() {
            try {
                Path indexPath = Paths.get(indexDir).toAbsolutePath();

                if (!Files.exists(indexPath)) {
                    System.err.println("Index directory does not exist: " + indexDir);
                    return 1;
                }

                try (LuceneIndexer indexer = new LuceneIndexer(indexPath)) {
                    List<SearchResult> results = indexer.listAllDocuments(maxResults);

                    if (jsonOutput) {
                        Map<String, Object> output = new LinkedHashMap<>();
                        output.put("totalDocuments", results.size());
                        output.put("documents", results);
                        System.out.println(gson.toJson(output));
                    } else {
                        System.out.println("Indexed documents: " + results.size() + "\n");

                        for (SearchResult r : results) {
                            System.out.println("- " + r.getFileName());
                            System.out.println("  Path: " + r.getFilePath());
                            System.out.println("  Size: " + r.getFormattedFileSize());
                            if (r.getLastModified() != null) {
                                System.out.println("  Modified: " + r.getLastModified());
                            }
                            if (r.getPageCount() > 0) {
                                System.out.println("  Pages: " + r.getPageCount());
                            }
                            System.out.println();
                        }
                    }
                }

                return 0;
            } catch (Exception e) {
                System.err.println("Error: " + e.getMessage());
                return 1;
            }
        }
    }

    // ========== 統計命令 ==========
    @Command(name = "stats", description = "Show index statistics")
    static class StatsCommand implements Callable<Integer> {

        @Option(names = {"-i", "--index-dir"}, description = "Index directory path", defaultValue = "./index-data")
        private String indexDir;

        @Option(names = {"--json"}, description = "Output as JSON")
        private boolean jsonOutput;

        @Override
        public Integer call() {
            try {
                Path indexPath = Paths.get(indexDir).toAbsolutePath();

                if (!Files.exists(indexPath)) {
                    System.err.println("Index directory does not exist: " + indexDir);
                    return 1;
                }

                try (LuceneIndexer indexer = new LuceneIndexer(indexPath)) {
                    Map<String, Object> stats = indexer.getStats();
                    stats.put("indexPath", indexPath.toString());

                    if (jsonOutput) {
                        System.out.println(gson.toJson(stats));
                    } else {
                        System.out.println("Index Statistics:");
                        System.out.println("  Index Path: " + indexPath);
                        System.out.println("  Total Documents: " + stats.get("totalDocuments"));
                        System.out.println("  Deleted Documents: " + stats.get("deletedDocuments"));
                    }
                }

                return 0;
            } catch (Exception e) {
                System.err.println("Error: " + e.getMessage());
                return 1;
            }
        }
    }

    // ========== 讀取命令 ==========
    @Command(name = "read", description = "Read content of a specific document by path")
    static class ReadCommand implements Callable<Integer> {

        @Parameters(index = "0", description = "File path to read")
        private String filePath;

        @Option(names = {"--json"}, description = "Output as JSON")
        private boolean jsonOutput;

        @Option(names = {"-l", "--limit"}, description = "Limit content length", defaultValue = "5000")
        private int limit;

        @Override
        public Integer call() {
            try {
                Path path = Paths.get(filePath).toAbsolutePath();

                if (!Files.exists(path)) {
                    System.err.println("File does not exist: " + filePath);
                    return 1;
                }

                TikaExtractor extractor = new TikaExtractor(limit);
                DocumentInfo doc = extractor.extract(path);

                if (jsonOutput) {
                    Map<String, Object> output = new LinkedHashMap<>();
                    output.put("filePath", doc.getFilePath());
                    output.put("fileName", doc.getFileName());
                    output.put("contentType", doc.getContentType());
                    output.put("fileSize", doc.getFileSize());
                    output.put("content", doc.getContent());
                    output.put("metadata", doc.getMetadata());
                    System.out.println(gson.toJson(output));
                } else {
                    System.out.println("File: " + doc.getFileName());
                    System.out.println("Path: " + doc.getFilePath());
                    System.out.println("Type: " + doc.getContentType());
                    System.out.println("Size: " + doc.getFileSize() + " bytes");
                    System.out.println("\n--- Content ---\n");
                    System.out.println(doc.getContent());
                }

                return 0;
            } catch (Exception e) {
                System.err.println("Error: " + e.getMessage());
                return 1;
            }
        }
    }

    // ========== 清除命令 ==========
    @Command(name = "clear", description = "Clear all indexed documents")
    static class ClearCommand implements Callable<Integer> {

        @Option(names = {"-i", "--index-dir"}, description = "Index directory path", defaultValue = "./index-data")
        private String indexDir;

        @Option(names = {"-f", "--force"}, description = "Force clear without confirmation")
        private boolean force;

        @Override
        public Integer call() {
            try {
                Path indexPath = Paths.get(indexDir).toAbsolutePath();

                if (!Files.exists(indexPath)) {
                    System.out.println("Index directory does not exist.");
                    return 0;
                }

                if (!force) {
                    System.out.print("Are you sure you want to clear all indexed documents? (y/N): ");
                    Scanner scanner = new Scanner(System.in);
                    String response = scanner.nextLine().trim().toLowerCase();
                    if (!response.equals("y") && !response.equals("yes")) {
                        System.out.println("Cancelled.");
                        return 0;
                    }
                }

                try (LuceneIndexer indexer = new LuceneIndexer(indexPath)) {
                    indexer.clearIndex();
                    System.out.println("Index cleared successfully.");
                }

                return 0;
            } catch (Exception e) {
                System.err.println("Error: " + e.getMessage());
                return 1;
            }
        }
    }
}
