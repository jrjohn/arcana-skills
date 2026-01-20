package com.docindex.core;

import com.docindex.model.DocumentInfo;
import org.apache.tika.Tika;
import org.apache.tika.exception.WriteLimitReachedException;
import org.apache.tika.exception.ZeroByteFileException;
import org.apache.tika.exception.EncryptedDocumentException;
import org.apache.tika.metadata.Metadata;
import org.apache.tika.metadata.TikaCoreProperties;
import org.apache.tika.parser.AutoDetectParser;
import org.apache.tika.parser.ParseContext;
import org.apache.tika.parser.ocr.TesseractOCRConfig;
import org.apache.tika.parser.pdf.PDFParserConfig;
import org.apache.tika.sax.BodyContentHandler;

import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.text.PDFTextStripper;

import java.io.File;
import java.io.FileInputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.attribute.BasicFileAttributes;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;
import java.util.regex.Pattern;

/**
 * 使用 Apache Tika 提取文件內容
 */
public class TikaExtractor {

    private final Tika tika;
    private final AutoDetectParser parser;
    private final int maxContentLength;

    // 分頁標記 (用於 Word 等文件)
    private static final Pattern PAGE_BREAK_PATTERN = Pattern.compile("\\f|\\x0C|<<<PAGE_BREAK>>>");

    // 支援的檔案類型
    private static final Set<String> SUPPORTED_EXTENSIONS = new HashSet<>(Arrays.asList(
        // 文件
        "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx",
        "odt", "ods", "odp", "rtf",
        // 文字
        "txt", "md", "markdown", "json", "xml", "yaml", "yml",
        "html", "htm", "csv", "tsv",
        // 程式碼
        "java", "py", "js", "ts", "c", "cpp", "h", "hpp",
        "cs", "go", "rs", "rb", "php", "swift", "kt",
        "sql", "sh", "bash", "zsh", "ps1",
        // 壓縮檔
        "zip", "tar", "gz", "7z", "rar",
        // 圖檔 (OCR)
        "png", "jpg", "jpeg", "gif", "bmp", "tiff", "tif", "webp",
        // 其他
        "log", "ini", "conf", "cfg", "properties"
    ));

    // 純文字檔案類型（可以用 fallback 讀取）
    private static final Set<String> TEXT_EXTENSIONS = new HashSet<>(Arrays.asList(
        "txt", "md", "markdown", "json", "xml", "yaml", "yml",
        "html", "htm", "csv", "tsv",
        "java", "py", "js", "ts", "c", "cpp", "h", "hpp",
        "cs", "go", "rs", "rb", "php", "swift", "kt",
        "sql", "sh", "bash", "zsh", "ps1",
        "log", "ini", "conf", "cfg", "properties"
    ));

    public TikaExtractor() {
        this(-1); // 無限制
    }

    public TikaExtractor(int maxContentLength) {
        this.tika = new Tika();
        this.parser = new AutoDetectParser();
        this.maxContentLength = maxContentLength;
    }

    /**
     * 從檔案提取文件資訊
     */
    public DocumentInfo extract(Path filePath) throws Exception {
        File file = filePath.toFile();
        if (!file.exists() || !file.isFile()) {
            throw new IllegalArgumentException("File does not exist: " + filePath);
        }

        // 跳過空檔案
        if (file.length() == 0) {
            throw new ZeroByteFileException("Empty file: " + filePath);
        }

        DocumentInfo docInfo = new DocumentInfo(filePath.toAbsolutePath().toString());
        docInfo.setFileName(file.getName());
        docInfo.setFileSize(file.length());

        // 檔案屬性
        BasicFileAttributes attrs = Files.readAttributes(filePath, BasicFileAttributes.class);
        docInfo.setLastModified(attrs.lastModifiedTime().toInstant());
        docInfo.setIndexedAt(Instant.now());

        // 產生文件 ID (使用檔案路徑的 hash)
        docInfo.setId(generateDocumentId(filePath.toAbsolutePath().toString()));

        String extension = getFileExtension(filePath).toLowerCase();

        // PDF 使用 PDFBox 分頁提取
        if ("pdf".equals(extension)) {
            extractPdfByPage(file, docInfo);
        } else {
            // 其他檔案使用 Tika 提取
            extractWithTika(file, docInfo);
        }

        return docInfo;
    }

    /**
     * PDF 分頁提取
     */
    private void extractPdfByPage(File file, DocumentInfo docInfo) {
        try (PDDocument document = PDDocument.load(file)) {
            int totalPages = document.getNumberOfPages();
            PDFTextStripper stripper = new PDFTextStripper();

            StringBuilder fullContent = new StringBuilder();

            for (int page = 1; page <= totalPages; page++) {
                stripper.setStartPage(page);
                stripper.setEndPage(page);
                String pageText = stripper.getText(document);

                if (pageText != null && !pageText.trim().isEmpty()) {
                    docInfo.addPageContent(pageText.trim());
                    fullContent.append(pageText);
                } else {
                    docInfo.addPageContent("");  // 空白頁
                }
            }

            docInfo.setContent(fullContent.toString().trim());
            docInfo.setContentType("application/pdf");
            docInfo.addMetadata("pageCount", String.valueOf(totalPages));

        } catch (Exception e) {
            // 如果 PDFBox 失敗，回退到 Tika
            extractWithTika(file, docInfo);
        }
    }

    /**
     * 使用 Tika 提取內容
     */
    private void extractWithTika(File file, DocumentInfo docInfo) {
        Metadata metadata = new Metadata();
        metadata.set(TikaCoreProperties.RESOURCE_NAME_KEY, file.getName());

        try (InputStream stream = new FileInputStream(file)) {
            BodyContentHandler handler = maxContentLength > 0
                ? new BodyContentHandler(maxContentLength)
                : new BodyContentHandler(-1);

            ParseContext context = new ParseContext();

            // 設定 OCR 配置
            TesseractOCRConfig ocrConfig = new TesseractOCRConfig();
            ocrConfig.setLanguage("chi_tra+chi_sim+eng");
            ocrConfig.setTimeoutSeconds(120);
            context.set(TesseractOCRConfig.class, ocrConfig);

            // 設定 PDF 配置
            PDFParserConfig pdfConfig = new PDFParserConfig();
            pdfConfig.setExtractInlineImages(true);
            pdfConfig.setOcrStrategy(PDFParserConfig.OCR_STRATEGY.AUTO);
            context.set(PDFParserConfig.class, pdfConfig);

            // 設定遞迴解析
            context.set(AutoDetectParser.class, parser);

            try {
                parser.parse(stream, handler, metadata, context);
            } catch (WriteLimitReachedException e) {
                // 內容長度限制，繼續處理
            }

            String content = handler.toString();
            docInfo.setContent(content != null ? content.trim() : "");

            // 嘗試按分頁標記分割
            if (content != null && !content.isEmpty()) {
                String[] pages = PAGE_BREAK_PATTERN.split(content);
                if (pages.length > 1) {
                    for (String page : pages) {
                        if (!page.trim().isEmpty()) {
                            docInfo.addPageContent(page.trim());
                        }
                    }
                } else {
                    // 無分頁標記，整個內容作為第一頁
                    docInfo.addPageContent(content.trim());
                }
            }

            String contentType = metadata.get(Metadata.CONTENT_TYPE);
            docInfo.setContentType(contentType != null ? contentType : "application/octet-stream");

            extractMetadata(metadata, docInfo);

        } catch (ZeroByteFileException | EncryptedDocumentException e) {
            docInfo.setContent("");
            docInfo.setContentType("application/octet-stream");
        } catch (Exception e) {
            Path filePath = file.toPath();
            if (isTextFile(filePath)) {
                fallbackExtract(filePath, docInfo);
            } else {
                docInfo.setContent("");
                docInfo.setContentType("application/octet-stream");
            }
        }
    }

    /**
     * 提取元數據
     */
    private void extractMetadata(Metadata metadata, DocumentInfo docInfo) {
        String title = metadata.get(TikaCoreProperties.TITLE);
        docInfo.addMetadata("title", title);

        String author = metadata.get(TikaCoreProperties.CREATOR);
        docInfo.addMetadata("author", author);

        if (metadata.getDate(TikaCoreProperties.CREATED) != null) {
            docInfo.addMetadata("created", metadata.getDate(TikaCoreProperties.CREATED).toString());
        }

        if (metadata.getDate(TikaCoreProperties.MODIFIED) != null) {
            docInfo.addMetadata("modified", metadata.getDate(TikaCoreProperties.MODIFIED).toString());
        }

        String pageCount = metadata.get("xmpTPg:NPages");
        if (pageCount == null) {
            pageCount = metadata.get("meta:page-count");
        }
        docInfo.addMetadata("pageCount", pageCount);

        String wordCount = metadata.get("meta:word-count");
        docInfo.addMetadata("wordCount", wordCount);
    }

    /**
     * 回退提取方法
     */
    private void fallbackExtract(Path filePath, DocumentInfo docInfo) {
        try {
            byte[] bytes = Files.readAllBytes(filePath);
            String content = new String(bytes, StandardCharsets.UTF_8);
            docInfo.setContent(content);
            docInfo.addPageContent(content);
            docInfo.setContentType("text/plain");
        } catch (Exception e) {
            docInfo.setContent("");
            docInfo.setContentType("application/octet-stream");
        }
    }

    /**
     * 檢查是否為文字檔案
     */
    private boolean isTextFile(Path filePath) {
        String extension = getFileExtension(filePath).toLowerCase();
        return TEXT_EXTENSIONS.contains(extension);
    }

    /**
     * 檢查檔案是否支援
     */
    public boolean isSupported(Path filePath) {
        String extension = getFileExtension(filePath).toLowerCase();
        return SUPPORTED_EXTENSIONS.contains(extension);
    }

    /**
     * 取得檔案副檔名
     */
    private String getFileExtension(Path filePath) {
        String fileName = filePath.getFileName().toString();
        int lastDot = fileName.lastIndexOf('.');
        return lastDot == -1 ? "" : fileName.substring(lastDot + 1);
    }

    /**
     * 產生文件 ID
     */
    private String generateDocumentId(String filePath) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            byte[] hash = md.digest(filePath.getBytes());
            StringBuilder sb = new StringBuilder();
            for (int i = 0; i < 8; i++) {
                sb.append(String.format("%02x", hash[i]));
            }
            return sb.toString();
        } catch (Exception e) {
            return String.valueOf(filePath.hashCode());
        }
    }

    /**
     * 偵測檔案 MIME 類型
     */
    public String detectMimeType(Path filePath) {
        try {
            return tika.detect(filePath);
        } catch (Exception e) {
            return "application/octet-stream";
        }
    }
}
