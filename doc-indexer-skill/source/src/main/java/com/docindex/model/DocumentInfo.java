package com.docindex.model;

import java.time.Instant;
import java.util.Map;
import java.util.HashMap;
import java.util.List;
import java.util.ArrayList;

/**
 * 文件資訊模型
 */
public class DocumentInfo {
    private String id;
    private String filePath;
    private String fileName;
    private String content;
    private String contentType;
    private long fileSize;
    private Instant lastModified;
    private Instant indexedAt;
    private Map<String, String> metadata;
    private List<String> pageContents;  // 分頁內容

    public DocumentInfo() {
        this.metadata = new HashMap<>();
        this.pageContents = new ArrayList<>();
    }

    public DocumentInfo(String filePath) {
        this();
        this.filePath = filePath;
    }

    // Getters and Setters
    public String getId() { return id; }
    public void setId(String id) { this.id = id; }

    public String getFilePath() { return filePath; }
    public void setFilePath(String filePath) { this.filePath = filePath; }

    public String getFileName() { return fileName; }
    public void setFileName(String fileName) { this.fileName = fileName; }

    public String getContent() { return content; }
    public void setContent(String content) { this.content = content; }

    public String getContentType() { return contentType; }
    public void setContentType(String contentType) { this.contentType = contentType; }

    public long getFileSize() { return fileSize; }
    public void setFileSize(long fileSize) { this.fileSize = fileSize; }

    public Instant getLastModified() { return lastModified; }
    public void setLastModified(Instant lastModified) { this.lastModified = lastModified; }

    public Instant getIndexedAt() { return indexedAt; }
    public void setIndexedAt(Instant indexedAt) { this.indexedAt = indexedAt; }

    public Map<String, String> getMetadata() { return metadata; }
    public void setMetadata(Map<String, String> metadata) { this.metadata = metadata; }

    public void addMetadata(String key, String value) {
        if (value != null && !value.isBlank()) {
            this.metadata.put(key, value);
        }
    }

    public String getMetadata(String key) {
        return this.metadata.get(key);
    }

    public List<String> getPageContents() { return pageContents; }
    public void setPageContents(List<String> pageContents) { this.pageContents = pageContents; }

    public void addPageContent(String content) {
        this.pageContents.add(content);
    }

    public int getPageCount() {
        return pageContents.isEmpty() ? 1 : pageContents.size();
    }

    @Override
    public String toString() {
        return String.format("DocumentInfo{id='%s', fileName='%s', contentType='%s', fileSize=%d, pages=%d}",
                id, fileName, contentType, fileSize, getPageCount());
    }
}
