package com.docindex.model;

import java.util.List;
import java.util.ArrayList;

/**
 * 搜尋結果模型
 */
public class SearchResult {
    private String documentId;
    private String filePath;
    private String fileName;
    private String contentType;
    private float score;
    private List<String> highlights;
    private String snippet;
    private long fileSize;
    private String lastModified;
    private String indexedAt;
    private int pageCount;
    private List<Integer> matchedPages;  // 匹配的頁碼

    public SearchResult() {
        this.highlights = new ArrayList<>();
        this.matchedPages = new ArrayList<>();
    }

    // Getters and Setters
    public String getDocumentId() { return documentId; }
    public void setDocumentId(String documentId) { this.documentId = documentId; }

    public String getFilePath() { return filePath; }
    public void setFilePath(String filePath) { this.filePath = filePath; }

    public String getFileName() { return fileName; }
    public void setFileName(String fileName) { this.fileName = fileName; }

    public String getContentType() { return contentType; }
    public void setContentType(String contentType) { this.contentType = contentType; }

    public float getScore() { return score; }
    public void setScore(float score) { this.score = score; }

    public List<String> getHighlights() { return highlights; }
    public void setHighlights(List<String> highlights) { this.highlights = highlights; }

    public String getSnippet() { return snippet; }
    public void setSnippet(String snippet) { this.snippet = snippet; }

    public long getFileSize() { return fileSize; }
    public void setFileSize(long fileSize) { this.fileSize = fileSize; }

    public String getLastModified() { return lastModified; }
    public void setLastModified(String lastModified) { this.lastModified = lastModified; }

    public String getIndexedAt() { return indexedAt; }
    public void setIndexedAt(String indexedAt) { this.indexedAt = indexedAt; }

    public int getPageCount() { return pageCount; }
    public void setPageCount(int pageCount) { this.pageCount = pageCount; }

    public List<Integer> getMatchedPages() { return matchedPages; }
    public void setMatchedPages(List<Integer> matchedPages) { this.matchedPages = matchedPages; }

    /**
     * 格式化匹配頁碼
     */
    public String getFormattedMatchedPages() {
        if (matchedPages == null || matchedPages.isEmpty()) {
            return "-";
        }
        if (matchedPages.size() == 1) {
            return "p." + matchedPages.get(0);
        }
        // 只顯示前3頁
        StringBuilder sb = new StringBuilder("p.");
        for (int i = 0; i < Math.min(3, matchedPages.size()); i++) {
            if (i > 0) sb.append(",");
            sb.append(matchedPages.get(i));
        }
        if (matchedPages.size() > 3) {
            sb.append("...(").append(matchedPages.size()).append("頁)");
        }
        return sb.toString();
    }

    /**
     * 格式化檔案大小
     */
    public String getFormattedFileSize() {
        if (fileSize < 1024) return fileSize + " B";
        if (fileSize < 1024 * 1024) return String.format("%.1f KB", fileSize / 1024.0);
        if (fileSize < 1024 * 1024 * 1024) return String.format("%.1f MB", fileSize / (1024.0 * 1024));
        return String.format("%.1f GB", fileSize / (1024.0 * 1024 * 1024));
    }

    @Override
    public String toString() {
        return String.format("SearchResult{fileName='%s', score=%.4f, snippet='%s...'}",
                fileName, score, snippet != null && snippet.length() > 50 ? snippet.substring(0, 50) : snippet);
    }
}
