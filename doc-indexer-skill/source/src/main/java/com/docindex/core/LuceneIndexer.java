package com.docindex.core;

import com.docindex.model.DocumentInfo;
import com.docindex.model.SearchResult;
import org.apache.lucene.analysis.Analyzer;
import org.apache.lucene.analysis.cn.smart.SmartChineseAnalyzer;
import org.apache.lucene.analysis.miscellaneous.PerFieldAnalyzerWrapper;
import org.apache.lucene.analysis.standard.StandardAnalyzer;
import org.apache.lucene.document.*;
import org.apache.lucene.index.*;
import org.apache.lucene.queryparser.classic.MultiFieldQueryParser;
import org.apache.lucene.queryparser.classic.QueryParser;
import org.apache.lucene.search.*;
import org.apache.lucene.store.Directory;
import org.apache.lucene.store.FSDirectory;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.nio.file.Path;
import java.util.*;

/**
 * Lucene 索引與搜尋服務
 */
public class LuceneIndexer implements AutoCloseable {
    private static final Logger logger = LoggerFactory.getLogger(LuceneIndexer.class);

    // 方案 C: 索引全部內容，不限制長度
    // 摘要將在搜尋時從原始檔案即時產生
    // 上下文摘要長度
    private static final int CONTEXT_LENGTH = 300;

    // 欄位名稱常數
    public static final String FIELD_ID = "id";
    public static final String FIELD_FILE_PATH = "filePath";
    public static final String FIELD_FILE_NAME = "fileName";
    public static final String FIELD_CONTENT = "content";
    public static final String FIELD_CONTENT_TYPE = "contentType";
    public static final String FIELD_FILE_SIZE = "fileSize";
    public static final String FIELD_LAST_MODIFIED = "lastModified";
    public static final String FIELD_INDEXED_AT = "indexedAt";
    public static final String FIELD_METADATA = "metadata";
    public static final String FIELD_PAGE_COUNT = "pageCount";
    public static final String FIELD_STORED_CONTENT = "storedContent";
    public static final String FIELD_PAGE_CONTENTS = "pageContents";  // 分頁內容（用 |PAGE:n| 分隔）

    private final Directory directory;
    private final Analyzer analyzer;
    private IndexWriter indexWriter;

    public LuceneIndexer(Path indexPath) throws IOException {
        this.directory = FSDirectory.open(indexPath);

        // 使用 SmartChineseAnalyzer 進行中文分詞
        this.analyzer = new SmartChineseAnalyzer();
    }

    /**
     * 開啟索引寫入器
     */
    public void openWriter() throws IOException {
        IndexWriterConfig config = new IndexWriterConfig(analyzer);
        config.setOpenMode(IndexWriterConfig.OpenMode.CREATE_OR_APPEND);
        this.indexWriter = new IndexWriter(directory, config);
    }

    /**
     * 索引單一文件
     */
    public void indexDocument(DocumentInfo docInfo) throws IOException {
        if (indexWriter == null) {
            openWriter();
        }

        Document doc = new Document();

        // ID (用於更新/刪除)
        doc.add(new StringField(FIELD_ID, docInfo.getId(), Field.Store.YES));

        // 檔案路徑 (精確匹配)
        doc.add(new StringField(FIELD_FILE_PATH, docInfo.getFilePath(), Field.Store.YES));

        // 檔案名稱 (可搜尋)
        doc.add(new TextField(FIELD_FILE_NAME, docInfo.getFileName(), Field.Store.YES));

        // 內容 (全文搜尋) - 方案 C: 索引全部內容，不限制長度
        if (docInfo.getContent() != null && !docInfo.getContent().isEmpty()) {
            String content = docInfo.getContent();
            // 索引完整內容（不限制長度）
            doc.add(new TextField(FIELD_CONTENT, content, Field.Store.NO));
            // 不再儲存內容用於摘要，摘要將在搜尋時從原始檔案即時產生
        }

        // 分頁內容 (用於匹配頁碼)
        List<String> pageContents = docInfo.getPageContents();
        if (pageContents != null && !pageContents.isEmpty()) {
            StringBuilder pageData = new StringBuilder();
            for (int i = 0; i < pageContents.size(); i++) {
                String pageContent = pageContents.get(i);
                // 限制每頁儲存的內容長度
                if (pageContent.length() > 2000) {
                    pageContent = pageContent.substring(0, 2000);
                }
                pageData.append("|PAGE:").append(i + 1).append("|");
                pageData.append(pageContent);
            }
            doc.add(new StoredField(FIELD_PAGE_CONTENTS, pageData.toString()));
        }

        // 頁數
        String pageCount = docInfo.getMetadata("pageCount");
        if (pageCount != null && !pageCount.isEmpty()) {
            try {
                int pages = Integer.parseInt(pageCount);
                doc.add(new IntPoint(FIELD_PAGE_COUNT, pages));
                doc.add(new StoredField(FIELD_PAGE_COUNT, pages));
            } catch (NumberFormatException e) {
                // 忽略無效的頁數
            }
        }

        // 內容類型
        if (docInfo.getContentType() != null) {
            doc.add(new StringField(FIELD_CONTENT_TYPE, docInfo.getContentType(), Field.Store.YES));
        }

        // 檔案大小
        doc.add(new LongPoint(FIELD_FILE_SIZE, docInfo.getFileSize()));
        doc.add(new StoredField(FIELD_FILE_SIZE, docInfo.getFileSize()));

        // 時間戳記
        if (docInfo.getLastModified() != null) {
            doc.add(new LongPoint(FIELD_LAST_MODIFIED, docInfo.getLastModified().toEpochMilli()));
            doc.add(new StoredField(FIELD_LAST_MODIFIED, docInfo.getLastModified().toString()));
        }

        if (docInfo.getIndexedAt() != null) {
            doc.add(new StoredField(FIELD_INDEXED_AT, docInfo.getIndexedAt().toString()));
        }

        // 元數據 (JSON 格式儲存)
        if (docInfo.getMetadata() != null && !docInfo.getMetadata().isEmpty()) {
            for (Map.Entry<String, String> entry : docInfo.getMetadata().entrySet()) {
                doc.add(new StoredField(FIELD_METADATA + "_" + entry.getKey(), entry.getValue()));
                // 也加入可搜尋欄位
                doc.add(new TextField(FIELD_METADATA, entry.getValue(), Field.Store.NO));
            }
        }

        // 使用 updateDocument 來處理重複文件
        indexWriter.updateDocument(new Term(FIELD_ID, docInfo.getId()), doc);
        logger.info("Indexed document: {}", docInfo.getFileName());
    }

    /**
     * 批次索引
     */
    public int indexDocuments(List<DocumentInfo> documents) throws IOException {
        int count = 0;
        for (DocumentInfo doc : documents) {
            try {
                indexDocument(doc);
                count++;
            } catch (Exception e) {
                logger.error("Failed to index document: {}", doc.getFilePath(), e);
            }
        }
        commit();
        return count;
    }

    /**
     * 刪除文件索引
     */
    public void deleteDocument(String documentId) throws IOException {
        if (indexWriter == null) {
            openWriter();
        }
        indexWriter.deleteDocuments(new Term(FIELD_ID, documentId));
    }

    /**
     * 搜尋文件
     */
    public List<SearchResult> search(String queryString, int maxResults) throws Exception {
        List<SearchResult> results = new ArrayList<>();

        try (DirectoryReader reader = DirectoryReader.open(directory)) {
            IndexSearcher searcher = new IndexSearcher(reader);

            // 多欄位搜尋，設定欄位權重
            String[] searchFields = {FIELD_CONTENT, FIELD_FILE_NAME, FIELD_METADATA};
            Map<String, Float> boosts = new HashMap<>();
            boosts.put(FIELD_FILE_NAME, 3.0f);  // 檔名權重 x3
            boosts.put(FIELD_CONTENT, 1.0f);    // 內容權重 x1
            boosts.put(FIELD_METADATA, 1.5f);   // 元數據權重 x1.5

            MultiFieldQueryParser parser = new MultiFieldQueryParser(searchFields, analyzer, boosts);
            parser.setDefaultOperator(QueryParser.Operator.OR);

            Query query = parser.parse(queryString);
            TopDocs topDocs = searcher.search(query, maxResults);

            for (ScoreDoc scoreDoc : topDocs.scoreDocs) {
                Document doc = searcher.storedFields().document(scoreDoc.doc);
                SearchResult result = new SearchResult();

                result.setDocumentId(doc.get(FIELD_ID));
                result.setFilePath(doc.get(FIELD_FILE_PATH));
                result.setFileName(doc.get(FIELD_FILE_NAME));
                result.setContentType(doc.get(FIELD_CONTENT_TYPE));
                result.setScore(scoreDoc.score);

                // 檔案大小
                IndexableField fileSizeField = doc.getField(FIELD_FILE_SIZE);
                if (fileSizeField != null) {
                    result.setFileSize(fileSizeField.numericValue().longValue());
                }

                // 修改日期
                result.setLastModified(doc.get(FIELD_LAST_MODIFIED));

                // 索引日期
                result.setIndexedAt(doc.get(FIELD_INDEXED_AT));

                // 頁數
                IndexableField pageCountField = doc.getField(FIELD_PAGE_COUNT);
                if (pageCountField != null) {
                    result.setPageCount(pageCountField.numericValue().intValue());
                }

                // 方案 C: 摘要將在 CLI 層從原始檔案即時產生
                // 不再從索引中的 storedContent 產生摘要

                // 找出匹配的頁碼
                String pageContents = doc.get(FIELD_PAGE_CONTENTS);
                if (pageContents != null) {
                    List<Integer> matchedPages = findMatchedPages(pageContents, queryString);
                    result.setMatchedPages(matchedPages);
                }

                results.add(result);
            }
        }

        return results;
    }

    /**
     * 取得所有已索引的文件
     */
    public List<SearchResult> listAllDocuments(int maxResults) throws IOException {
        List<SearchResult> results = new ArrayList<>();

        try (DirectoryReader reader = DirectoryReader.open(directory)) {
            IndexSearcher searcher = new IndexSearcher(reader);
            TopDocs topDocs = searcher.search(new MatchAllDocsQuery(), maxResults);

            for (ScoreDoc scoreDoc : topDocs.scoreDocs) {
                Document doc = searcher.storedFields().document(scoreDoc.doc);
                SearchResult result = new SearchResult();

                result.setDocumentId(doc.get(FIELD_ID));
                result.setFilePath(doc.get(FIELD_FILE_PATH));
                result.setFileName(doc.get(FIELD_FILE_NAME));
                result.setContentType(doc.get(FIELD_CONTENT_TYPE));
                result.setScore(scoreDoc.score);

                // 檔案大小
                IndexableField fileSizeField = doc.getField(FIELD_FILE_SIZE);
                if (fileSizeField != null) {
                    result.setFileSize(fileSizeField.numericValue().longValue());
                }

                // 修改日期
                result.setLastModified(doc.get(FIELD_LAST_MODIFIED));

                // 頁數
                IndexableField pageCountField = doc.getField(FIELD_PAGE_COUNT);
                if (pageCountField != null) {
                    result.setPageCount(pageCountField.numericValue().intValue());
                }

                results.add(result);
            }
        }

        return results;
    }

    /**
     * 取得索引統計資訊
     */
    public Map<String, Object> getStats() throws IOException {
        Map<String, Object> stats = new HashMap<>();

        try (DirectoryReader reader = DirectoryReader.open(directory)) {
            stats.put("totalDocuments", reader.numDocs());
            stats.put("deletedDocuments", reader.numDeletedDocs());
            stats.put("maxDocuments", reader.maxDoc());
        }

        return stats;
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

    /**
     * 找出匹配的頁碼
     */
    private List<Integer> findMatchedPages(String pageContents, String query) {
        List<Integer> matchedPages = new ArrayList<>();
        String[] queryTerms = query.toLowerCase().split("\\s+");

        // 解析分頁內容
        String[] parts = pageContents.split("\\|PAGE:");
        for (String part : parts) {
            if (part.isEmpty()) continue;

            int pipePos = part.indexOf('|');
            if (pipePos == -1) continue;

            try {
                int pageNum = Integer.parseInt(part.substring(0, pipePos));
                String pageText = part.substring(pipePos + 1).toLowerCase();

                // 檢查每個查詢詞是否在此頁出現
                for (String term : queryTerms) {
                    String cleanTerm = term.replaceAll("[^\\p{L}\\p{N}]", "");
                    if (!cleanTerm.isEmpty() && pageText.contains(cleanTerm)) {
                        if (!matchedPages.contains(pageNum)) {
                            matchedPages.add(pageNum);
                        }
                        break;
                    }
                }
            } catch (NumberFormatException e) {
                // 忽略解析錯誤
            }
        }

        Collections.sort(matchedPages);
        return matchedPages;
    }

    /**
     * 提交變更
     */
    public void commit() throws IOException {
        if (indexWriter != null) {
            indexWriter.commit();
        }
    }

    /**
     * 清除所有索引
     */
    public void clearIndex() throws IOException {
        if (indexWriter == null) {
            openWriter();
        }
        indexWriter.deleteAll();
        indexWriter.commit();
    }

    @Override
    public void close() throws IOException {
        if (indexWriter != null) {
            indexWriter.close();
        }
        directory.close();
    }
}
