#!/usr/bin/env node
/**
 * UI Flow Navigation Validation Script
 *
 * 驗證所有 HTML 畫面的可點擊元素是否有正確的導航目標
 * 此腳本不依賴 puppeteer，可直接執行
 *
 * Usage:
 *   node validate-navigation.js [--fix] [--report]
 *
 * Options:
 *   --fix     輸出修復建議
 *   --report  輸出詳細 Markdown 報告
 */

const fs = require('fs');
const path = require('path');

// Configuration
const config = {
  // 掃描目錄（相對於腳本位置）
  scanDirs: [
    './',
    './auth',
    './home',
    './vocab',
    './train',
    './report',
    './setting',
    './engage',      // 互動獎勵模組
    './progress',    // 進度統計模組
    './social',      // 社群模組
    './common',      // 共用狀態畫面
    './profile',     // 個人資料模組
    './parent',      // 家長控制模組
    './iphone',
  ],
  // 排除的檔案/目錄
  excludePatterns: ['node_modules', 'shared', 'docs', 'screenshots', 'device-preview.html', 'screen-template'],
  // 有效的外部導航
  validExternalPatterns: ['http://', 'https://', 'mailto:', 'tel:', 'javascript:'],
};

// Results storage
const results = {
  totalScreens: 0,
  totalElements: 0,
  validElements: 0,
  invalidElements: 0,
  screens: [],
  issues: [],
};

/**
 * 掃描目錄取得所有 HTML 檔案
 */
function getHtmlFiles(baseDir) {
  const files = [];

  for (const dir of config.scanDirs) {
    const fullPath = path.join(baseDir, dir);
    if (!fs.existsSync(fullPath)) continue;

    const entries = fs.readdirSync(fullPath, { withFileTypes: true });
    for (const entry of entries) {
      if (entry.isFile() && entry.name.endsWith('.html')) {
        const filePath = path.join(fullPath, entry.name);
        const relativePath = path.relative(baseDir, filePath);

        // Check exclusions
        const shouldExclude = config.excludePatterns.some(pattern =>
          relativePath.includes(pattern)
        );

        if (!shouldExclude) {
          files.push({ path: filePath, relative: relativePath });
        }
      }
    }
  }

  return files;
}

/**
 * 從 HTML 內容提取可點擊元素
 */
function extractClickableElements(htmlContent, filePath) {
  const elements = [];
  const baseDir = path.dirname(filePath);

  // 1. 提取 onclick="location.href='...'" 模式
  const onclickHrefRegex = /onclick\s*=\s*["'](?:[^"']*)?location\.href\s*=\s*['"]([^'"]+)['"]/gi;
  let match;
  while ((match = onclickHrefRegex.exec(htmlContent)) !== null) {
    elements.push({
      type: 'onclick-href',
      target: match[1],
      raw: match[0],
      lineNumber: getLineNumber(htmlContent, match.index),
    });
  }

  // 2. 提取 href="..." 模式 (排除 #)
  const hrefRegex = /<a[^>]+href\s*=\s*["']([^"'#][^"']*)["']/gi;
  while ((match = hrefRegex.exec(htmlContent)) !== null) {
    elements.push({
      type: 'href',
      target: match[1],
      raw: match[0],
      lineNumber: getLineNumber(htmlContent, match.index),
    });
  }

  // 3. 檢測問題模式

  // 3a. href="#" (空連結)
  const emptyHrefRegex = /href\s*=\s*["']#["']/gi;
  while ((match = emptyHrefRegex.exec(htmlContent)) !== null) {
    elements.push({
      type: 'empty-href',
      target: '#',
      raw: match[0],
      lineNumber: getLineNumber(htmlContent, match.index),
      isIssue: true,
      issue: 'Empty href="#" has no navigation target',
    });
  }

  // 3b. onclick="" (空 onclick)
  const emptyOnclickRegex = /onclick\s*=\s*["']\s*["']/gi;
  while ((match = emptyOnclickRegex.exec(htmlContent)) !== null) {
    elements.push({
      type: 'empty-onclick',
      target: '',
      raw: match[0],
      lineNumber: getLineNumber(htmlContent, match.index),
      isIssue: true,
      issue: 'Empty onclick="" has no action',
    });
  }

  // 3b2. onclick="void(0)" (佔位符 onclick - 潛在問題)
  const voidOnclickRegex = /<(?:button|a|div)[^>]*onclick\s*=\s*["'](?:javascript:)?void\s*\(\s*0\s*\)["'][^>]*>/gi;
  while ((match = voidOnclickRegex.exec(htmlContent)) !== null) {
    const tag = match[0];
    const lineNumber = getLineNumber(htmlContent, match.index);

    // 提取元素 ID
    const idMatch = tag.match(/id\s*=\s*["']([^"']+)["']/i);
    const elementId = idMatch ? idMatch[1] : '(no id)';

    // 提取元素文字內容 (查找到結束標籤)
    const tagName = tag.match(/<(\w+)/)?.[1] || 'element';
    const closeTagPos = htmlContent.indexOf(`</${tagName}>`, match.index);
    const elementContent = closeTagPos > match.index
      ? htmlContent.substring(match.index, closeTagPos + tagName.length + 3)
      : tag;
    const textContent = extractTextContent(elementContent);

    // 判斷是否為導航按鈕 (有 chevron 圖標或特定命名)
    const isNavigationButton = detectSettingsRow(elementContent) ||
      elementId.startsWith('cell_') ||
      elementId.startsWith('btn_') ||
      elementId.startsWith('lnk_') ||
      elementId.startsWith('nav_');

    // 判斷是否為外部連結 (可接受使用 void(0))
    const isExternalLink = textContent.includes('評價') ||
      textContent.includes('評分') ||
      textContent.includes('App Store') ||
      elementId.includes('rate') ||
      elementId.includes('external');

    if (isNavigationButton && !isExternalLink) {
      elements.push({
        type: 'void-onclick-navigation',
        target: 'void(0)',
        raw: tag.substring(0, 80) + (tag.length > 80 ? '...' : ''),
        lineNumber: lineNumber,
        isIssue: true,
        issue: `⚠️ Navigation button [${elementId}] uses void(0) - needs real target`,
        textContent: textContent,
        elementId: elementId,
      });
    } else if (!isExternalLink) {
      // 非導航按鈕但也使用 void(0)，記錄為警告
      elements.push({
        type: 'void-onclick-warning',
        target: 'void(0)',
        raw: tag.substring(0, 80) + (tag.length > 80 ? '...' : ''),
        lineNumber: lineNumber,
        isIssue: false, // 不計入錯誤，但會顯示警告
        issue: `ℹ️ Element [${elementId}] uses void(0) - acceptable for UI interactions`,
        textContent: textContent,
        elementId: elementId,
      });
    }
  }

  // 3c. button 無 onclick (檢查是否在可點擊區域內)
  const buttonRegex = /<button[^>]*>[\s\S]*?<\/button>/gi;
  while ((match = buttonRegex.exec(htmlContent)) !== null) {
    const buttonFull = match[0];
    const buttonTag = buttonFull.match(/<button[^>]*>/i)?.[0] || '';

    // 跳過已有 onclick 的按鈕
    if (buttonTag.includes('onclick=')) continue;

    // 檢查是否為關閉/離開按鈕
    const isCloseButton = detectCloseButton(buttonFull);

    // 檢查是否為設定列表行按鈕 (有 chevron-right 圖標)
    const isSettingsRow = detectSettingsRow(buttonFull);

    // 跳過 type="submit" 在 form 內的按鈕 (可能由 form 處理)
    if (!buttonTag.includes('type="submit"')) {
      let issueType, issueMsg;

      if (isCloseButton) {
        issueType = 'close-button-no-onclick';
        issueMsg = '⚠️ CRITICAL: Close/Exit button has no onclick handler (must navigate back)';
      } else if (isSettingsRow) {
        issueType = 'settings-row-no-onclick';
        issueMsg = '⚠️ CRITICAL: Settings row has no onclick handler (must navigate or show alert)';
      } else {
        issueType = 'button-no-onclick';
        issueMsg = 'Button has no onclick handler';
      }

      // 提取按鈕文字內容以供修復建議使用
      const textContent = extractTextContent(buttonFull);

      elements.push({
        type: issueType,
        target: null,
        raw: buttonTag.substring(0, 80) + (buttonTag.length > 80 ? '...' : ''),
        lineNumber: getLineNumber(htmlContent, match.index),
        isIssue: true,
        issue: issueMsg,
        isCloseButton: isCloseButton,
        isSettingsRow: isSettingsRow,
        textContent: textContent, // 儲存文字內容
      });
    }
  }

  // 3d. 檢測獨立的關閉圖標 (div/span 包含 X SVG 但無 onclick)
  // 修正: 只匹配小範圍的 div/span (< 500 字元), 避免匹配整個容器 div
  const closeIconRegex = /<(?:div|span)[^>]*>[\s\S]{0,400}?(?:M6 18L18 6|M6 6l12 12|×|✕|✖)[\s\S]{0,100}?<\/(?:div|span)>/gi;
  while ((match = closeIconRegex.exec(htmlContent)) !== null) {
    const element = match[0];
    const openTag = element.match(/<(?:div|span)[^>]*>/i)?.[0] || '';

    // 跳過已有 onclick 的元素
    if (openTag.includes('onclick=')) continue;

    // 跳過裝飾性元素 (aria-hidden, role="presentation", pointer-events-none)
    if (openTag.includes('aria-hidden="true"') || openTag.includes('role="presentation"') || openTag.includes('pointer-events-none')) continue;

    // 跳過容器 div (通常有 flex, w-full, h-full 等 class)
    if (openTag.includes('flex-col') || openTag.includes('w-full') || openTag.includes('h-full')) continue;

    // 跳過如果 X 圖標在 button 內 (button 已在 3c 處理)
    // 檢查這段 HTML 中是否有包含 onclick 的 button
    if (element.includes('<button') && element.includes('onclick=')) continue;

    // 檢查是否真的是關閉圖標
    // 排除 ×1, ×2, ×3 等乘法符號
    const hasXIcon = element.includes('M6 18L18 6') || element.includes('M6 6l12 12') ||
        element.includes('✕') || element.includes('✖');
    const hasMultiplySign = element.includes('×') && !element.match(/×\d/);

    // 跳過裝飾性 X 圖標 (有 aria-hidden, role="presentation", 或 pointer-events-none)
    if (element.includes('aria-hidden="true"') || element.includes('role="presentation"') || element.includes('pointer-events-none')) continue;

    if (hasXIcon || (element.includes('×') && hasMultiplySign)) {
      elements.push({
        type: 'close-icon-no-onclick',
        target: null,
        raw: openTag.substring(0, 60) + '...',
        lineNumber: getLineNumber(htmlContent, match.index),
        isIssue: true,
        issue: '⚠️ CRITICAL: Close icon (X) has no onclick handler',
        isCloseButton: true,
      });
    }
  }

  // 3e. 檢測可點擊列表行 (有 active:bg-* 或 hover:bg-* 但無 onclick)
  // 注意: 跳過 <button> 因為已在 3c 處理
  // 注意: 跳過 group-hover 和 group-active (子元素樣式，不是獨立可點擊)
  const clickableRowRegex = /<(?:div|a)[^>]*(?:active:|hover:)[^>]*>/gi;
  while ((match = clickableRowRegex.exec(htmlContent)) !== null) {
    const tag = match[0];

    // 跳過已有 onclick 或 href (非 #) 的元素
    if (tag.includes('onclick=')) continue;
    if (tag.includes('href=') && !tag.includes('href="#"')) continue;

    // 跳過 group-hover 和 group-active (子元素樣式，由父元素控制)
    if (tag.includes('group-hover:') || tag.includes('group-active:')) continue;

    // 檢查是否有 active:bg- 或 hover:bg- (表示可點擊樣式)
    if (tag.match(/(?:active:|hover:)bg-/)) {
      // 嘗試提取完整元素內容來識別功能
      const elementMatch = htmlContent.substring(match.index).match(/<(?:div|a)[^>]*>[\s\S]*?<\/(?:div|a)>/i);
      const elementContent = elementMatch ? elementMatch[0] : tag;

      // 識別是否為設定列表行 (使用 detectSettingsRow 函數)
      const isSettingsRow = detectSettingsRow(elementContent);

      const issueType = isSettingsRow ? 'settings-row-no-onclick' : 'clickable-row-no-onclick';
      const issueMsg = isSettingsRow
        ? '⚠️ CRITICAL: Settings row has no onclick handler (must navigate or show alert)'
        : '⚠️ Clickable row (has active/hover style) has no onclick handler';

      elements.push({
        type: issueType,
        target: null,
        raw: tag.substring(0, 80) + (tag.length > 80 ? '...' : ''),
        lineNumber: getLineNumber(htmlContent, match.index),
        isIssue: true,
        issue: issueMsg,
        isSettingsRow: isSettingsRow,
      });
    }
  }

  return elements;
}

/**
 * 檢測按鈕是否為關閉/離開按鈕
 */
function detectCloseButton(buttonHtml) {
  const lowerHtml = buttonHtml.toLowerCase();

  // 1. 檢查 SVG X 形狀路徑 (對角線)
  const xPathPatterns = [
    'M6 18L18 6',      // 標準 X 路徑
    'M6 6l12 12',      // 另一種 X 路徑
    'm6 18l12-12',     // 相對路徑版本
    'm6 6l12 12',
    'M18 6L6 18',      // 反向
    'M4 4L20 20',      // 大一點的 X
    'M20 4L4 20',
  ];

  for (const pattern of xPathPatterns) {
    if (buttonHtml.includes(pattern) || lowerHtml.includes(pattern.toLowerCase())) {
      return true;
    }
  }

  // 2. 檢查 class 名稱
  const closeClassPatterns = [
    'close', 'dismiss', 'exit', 'cancel',
    'back', 'return', 'leave', 'quit'
  ];

  for (const pattern of closeClassPatterns) {
    if (lowerHtml.includes(`class="`) && lowerHtml.includes(pattern)) {
      return true;
    }
  }

  // 3. 檢查 X 文字符號
  const xSymbols = ['×', '✕', '✖', '╳', '&times;'];
  for (const symbol of xSymbols) {
    if (buttonHtml.includes(symbol)) {
      return true;
    }
  }

  // 4. 檢查 aria-label
  if (lowerHtml.includes('aria-label="close"') ||
      lowerHtml.includes('aria-label="關閉"') ||
      lowerHtml.includes('aria-label="離開"')) {
    return true;
  }

  return false;
}

/**
 * 檢測是否為設定列表行 (有 chevron-right 圖標)
 */
function detectSettingsRow(elementHtml) {
  // 1. 檢查 chevron-right SVG 路徑 (多種格式)
  const chevronPatterns = [
    'M9 5l7 7-7 7',        // 標準 chevron-right
    'M9 5 l7 7 -7 7',      // 有空格版本
    'm9 5l7 7-7 7',        // 小寫版本
    'M8.59 16.59L13.17 12 8.59 7.41',  // Material Design chevron
    'M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z',  // 另一種 MD chevron
  ];

  for (const pattern of chevronPatterns) {
    if (elementHtml.includes(pattern)) {
      return true;
    }
  }

  // 2. 檢查常見的 chevron class 名稱
  const lowerHtml = elementHtml.toLowerCase();
  const chevronClassPatterns = [
    'chevron-right',
    'chevron_right',
    'arrow-right',
    'arrow_right',
    'icon-right',
  ];

  for (const pattern of chevronClassPatterns) {
    if (lowerHtml.includes(pattern)) {
      return true;
    }
  }

  // 3. 檢查 › 或 > 符號 (作為導航指示)
  if (elementHtml.includes('›') || elementHtml.includes('&gt;') || elementHtml.includes('→')) {
    // 確認這是作為導航指示而非其他用途 (需要有 active/hover 樣式)
    if (lowerHtml.includes('active:') || lowerHtml.includes('hover:')) {
      return true;
    }
  }

  return false;
}

/**
 * 從 HTML 中提取文字內容 (移除 HTML 標籤)
 */
function extractTextContent(html) {
  // 移除 SVG 內容
  let text = html.replace(/<svg[\s\S]*?<\/svg>/gi, '');
  // 移除所有 HTML 標籤
  text = text.replace(/<[^>]+>/g, ' ');
  // 清理多餘空白
  text = text.replace(/\s+/g, ' ').trim();
  return text;
}

/**
 * 根據文字內容預測目標畫面 ID
 */
function predictTargetScreen(textContent, screenPath) {
  // 設定功能對照表
  const settingsMap = {
    '個人資料': { id: 'profile', desc: '編輯您的個人資訊' },
    '帳號安全': { id: 'security', desc: '管理密碼和安全設定' },
    '密碼': { id: 'password', desc: '變更密碼' },
    '通知設定': { id: 'notification', desc: '管理通知偏好' },
    '通知': { id: 'notification', desc: '管理通知偏好' },
    '偏好設定': { id: 'preferences', desc: '個人化設定' },
    '語言': { id: 'language', desc: '變更應用程式語言' },
    '主題': { id: 'theme', desc: '變更外觀主題' },
    '外觀': { id: 'appearance', desc: '變更外觀設定' },
    '深色模式': { id: 'darkmode', desc: '切換深色模式' },
    '隱私': { id: 'privacy', desc: '隱私權設定' },
    '隱私權': { id: 'privacy', desc: '隱私權設定' },
    '資料備份': { id: 'backup', desc: '備份和還原資料' },
    '備份': { id: 'backup', desc: '備份和還原資料' },
    '同步': { id: 'sync', desc: '同步設定' },
    '幫助': { id: 'help', desc: '取得幫助和支援' },
    '說明': { id: 'help', desc: '取得幫助和支援' },
    '客服': { id: 'support', desc: '聯繫客戶服務' },
    '支援': { id: 'support', desc: '聯繫客戶服務' },
    '意見回饋': { id: 'feedback', desc: '提供使用意見' },
    '回饋': { id: 'feedback', desc: '提供使用意見' },
    '關於': { id: 'about', desc: '查看應用程式資訊' },
    '版本': { id: 'version', desc: '查看版本資訊' },
    '條款': { id: 'terms', desc: '查看使用條款' },
    '使用條款': { id: 'terms', desc: '查看使用條款' },
    '服務條款': { id: 'terms', desc: '查看服務條款' },
    '學習設定': { id: 'learning', desc: '調整學習偏好' },
    '學習偏好': { id: 'learning', desc: '調整學習偏好' },
    '聲音': { id: 'sound', desc: '調整聲音設定' },
    '音效': { id: 'sound', desc: '調整音效設定' },
    '訂閱': { id: 'subscription', desc: '管理訂閱方案' },
    '付款': { id: 'payment', desc: '管理付款方式' },
    '登出': { id: 'logout', desc: '登出帳號' },
    '刪除帳號': { id: 'delete-account', desc: '刪除您的帳號' },
    '語音設定': { id: 'voice', desc: '調整發音速度和音量' },
    '語音': { id: 'voice', desc: '調整語音設定' },
    '資料管理': { id: 'data', desc: '管理您的資料' },
    '資料': { id: 'data', desc: '管理資料設定' },
    '清除快取': { id: 'cache', desc: '清除暫存資料' },
    '快取': { id: 'cache', desc: '清除快取' },
    '分享': { id: 'share', desc: '分享應用程式' },
    '邀請': { id: 'invite', desc: '邀請好友使用' },
    '評分': { id: 'rate', desc: '前往 App Store 評分' },
    '聯絡我們': { id: 'contact', desc: '聯繫客戶支援' },
    '常見問題': { id: 'faq', desc: '查看常見問題' },
    'FAQ': { id: 'faq', desc: '查看常見問題' },
  };

  // 從畫面路徑提取模組名稱 (e.g., "setting/SCR-SETTING-001" -> "SETTING")
  const moduleMatch = screenPath.match(/SCR-([A-Z]+)-/);
  const module = moduleMatch ? moduleMatch[1] : 'SETTING';

  // 尋找匹配的設定項目
  for (const [key, value] of Object.entries(settingsMap)) {
    if (textContent.includes(key)) {
      // 計算下一個序號 (假設從 002 開始)
      const screenId = `SCR-${module}-002-${value.id}.html`;
      return {
        screenId: screenId,
        description: value.desc,
        matched: key,
      };
    }
  }

  // 無法匹配時，產生對應畫面
  // 使用文字內容的前幾個字產生畫面 ID
  const cleanText = textContent.replace(/\s+/g, '-').substring(0, 15);
  const generatedId = cleanText.toLowerCase()
    .replace(/[^\u4e00-\u9fa5a-z0-9-]/g, '') // 只保留中文、英文、數字、連字號
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '');

  const fallbackScreenId = generatedId
    ? `SCR-${module}-002-${generatedId}.html`
    : `SCR-${module}-002-detail.html`;

  return {
    screenId: fallbackScreenId,
    description: textContent.substring(0, 20) + '設定',
    matched: null,
  };
}

/**
 * 取得行號
 */
function getLineNumber(content, index) {
  return content.substring(0, index).split('\n').length;
}

/**
 * 驗證目標是否存在
 */
function validateTarget(target, baseDir, allFiles) {
  // 外部連結
  if (config.validExternalPatterns.some(p => target.startsWith(p))) {
    return { valid: true, type: 'external' };
  }

  // alert() 呼叫
  if (target.includes('alert(')) {
    return { valid: true, type: 'alert' };
  }

  // 相對路徑解析
  const resolvedPath = path.resolve(baseDir, target);
  const relativePath = path.relative(process.cwd(), resolvedPath);

  // 檢查檔案是否存在
  if (fs.existsSync(resolvedPath)) {
    return { valid: true, type: 'file', path: relativePath };
  }

  // 檢查是否在已知檔案列表中
  const matchedFile = allFiles.find(f =>
    f.relative === relativePath ||
    f.relative.endsWith(target) ||
    target.endsWith(path.basename(f.relative))
  );

  if (matchedFile) {
    return { valid: true, type: 'matched', path: matchedFile.relative };
  }

  return { valid: false, type: 'missing', path: relativePath };
}

/**
 * 主要驗證函數
 */
function validateNavigation(baseDir) {
  console.log('🔍 UI Flow Navigation Validation\n');
  console.log(`Base Directory: ${baseDir}\n`);

  // 取得所有 HTML 檔案
  const htmlFiles = getHtmlFiles(baseDir);
  results.totalScreens = htmlFiles.length;

  console.log(`Found ${htmlFiles.length} HTML files to validate\n`);
  console.log('─'.repeat(60) + '\n');

  // 驗證每個檔案
  for (const file of htmlFiles) {
    const content = fs.readFileSync(file.path, 'utf-8');
    const elements = extractClickableElements(content, file.path);

    const screenResult = {
      screen: file.relative,
      totalElements: elements.length,
      validElements: 0,
      issues: [],
    };

    // 檢查 notify-parent.js 引入 (排除 index.html 和 device-preview.html)
    const filename = path.basename(file.path);
    if (filename !== 'index.html' && filename !== 'device-preview.html') {
      if (!content.includes('notify-parent.js')) {
        screenResult.issues.push({
          type: 'missing-notify-parent',
          line: 0,
          issue: '⚠️ Missing notify-parent.js - Sidebar will not sync when navigating to this screen',
          raw: 'Add: <script src="../shared/notify-parent.js"></script>',
        });
        results.issues.push({
          screen: file.relative,
          type: 'missing-notify-parent',
          lineNumber: 0,
          issue: 'Missing notify-parent.js script',
        });
        results.invalidElements++;
      }
    }

    // 檢查 device-preview.html 的 postMessage 監聽器和 sidebar sync 函數
    if (filename === 'device-preview.html') {
      // 檢查 postMessage 監聽器
      if (!content.includes('addEventListener') || !content.includes('pageLoaded')) {
        screenResult.issues.push({
          type: 'missing-postmessage-listener',
          line: 0,
          issue: '⚠️ CRITICAL: Missing postMessage listener - Sidebar will not sync on navigation',
          raw: 'Add: window.addEventListener(\'message\', ...) with pageLoaded handler',
        });
        results.issues.push({
          screen: file.relative,
          type: 'missing-postmessage-listener',
          lineNumber: 0,
          issue: 'Missing postMessage listener for sidebar sync',
        });
        results.invalidElements++;
      }

      // 檢查 syncSidebarFromIframe 函數
      if (!content.includes('syncSidebarFromIframe')) {
        screenResult.issues.push({
          type: 'missing-sidebar-sync-function',
          line: 0,
          issue: '⚠️ CRITICAL: Missing syncSidebarFromIframe function - Sidebar will not highlight current screen',
          raw: 'Add: function syncSidebarFromIframe(url) { ... }',
        });
        results.issues.push({
          screen: file.relative,
          type: 'missing-sidebar-sync-function',
          lineNumber: 0,
          issue: 'Missing syncSidebarFromIframe function',
        });
        results.invalidElements++;
      }

      // 檢查 data-screen 屬性 (用於 sidebar sync)
      const screenItemsCount = (content.match(/class="screen-item/g) || []).length;
      const dataScreenCount = (content.match(/data-screen="/g) || []).length;
      if (screenItemsCount > 0 && dataScreenCount < screenItemsCount) {
        screenResult.issues.push({
          type: 'missing-data-screen-attributes',
          line: 0,
          issue: `⚠️ WARNING: ${screenItemsCount - dataScreenCount} screen items missing data-screen attribute - Sidebar sync may not work properly`,
          raw: 'Add: data-screen="module/SCR-XXX.html" to each screen-item',
        });
        results.issues.push({
          screen: file.relative,
          type: 'missing-data-screen-attributes',
          lineNumber: 0,
          issue: `${screenItemsCount - dataScreenCount} screen items missing data-screen attribute`,
        });
        // Don't count as invalid element, just a warning
      }
    }

    for (const element of elements) {
      results.totalElements++;

      if (element.isIssue) {
        // 已標記的問題
        screenResult.issues.push({
          type: element.type,
          line: element.lineNumber,
          issue: element.issue,
          raw: element.raw,
        });
        results.issues.push({
          screen: file.relative,
          ...element,
        });
        results.invalidElements++;
      } else if (element.target) {
        // 驗證目標
        const validation = validateTarget(element.target, path.dirname(file.path), htmlFiles);

        if (validation.valid) {
          screenResult.validElements++;
          results.validElements++;
        } else {
          screenResult.issues.push({
            type: element.type,
            line: element.lineNumber,
            issue: `Target not found: ${element.target}`,
            raw: element.raw,
          });
          results.issues.push({
            screen: file.relative,
            type: element.type,
            target: element.target,
            lineNumber: element.lineNumber,
            issue: `Target not found: ${element.target}`,
          });
          results.invalidElements++;
        }
      }
    }

    results.screens.push(screenResult);

    // 輸出每個畫面的結果
    const status = screenResult.issues.length === 0 ? '✅' : '⚠️';
    console.log(`${status} ${file.relative}`);
    console.log(`   Elements: ${screenResult.totalElements}, Valid: ${screenResult.validElements}, Issues: ${screenResult.issues.length}`);

    if (screenResult.issues.length > 0) {
      for (const issue of screenResult.issues) {
        console.log(`   ❌ Line ${issue.line}: ${issue.issue}`);
      }
    }
    console.log('');
  }

  // 輸出總結
  console.log('─'.repeat(60));
  console.log('\n📊 Summary\n');

  const coverage = results.totalElements > 0
    ? ((results.validElements / results.totalElements) * 100).toFixed(1)
    : 100;

  console.log(`Total Screens:    ${results.totalScreens}`);
  console.log(`Total Elements:   ${results.totalElements}`);
  console.log(`Valid Elements:   ${results.validElements}`);
  console.log(`Invalid Elements: ${results.invalidElements}`);
  console.log(`Coverage:         ${coverage}%`);
  console.log('');

  if (results.invalidElements > 0) {
    console.log('⚠️  Navigation validation FAILED - issues found');
    console.log('   Run with --fix to see fix suggestions');
  } else {
    console.log('✅ Navigation validation PASSED - 100% coverage');
  }

  return results;
}

/**
 * 生成 Markdown 報告
 */
function generateReport(results) {
  const coverage = results.totalElements > 0
    ? ((results.validElements / results.totalElements) * 100).toFixed(1)
    : 100;

  let report = `# Navigation Validation Report

**Generated:** ${new Date().toISOString()}
**Coverage:** ${coverage}%

## Summary

| Metric | Value |
|--------|-------|
| Total Screens | ${results.totalScreens} |
| Total Clickable Elements | ${results.totalElements} |
| Valid Elements | ${results.validElements} |
| Invalid Elements | ${results.invalidElements} |
| **Coverage** | **${coverage}%** |

## Screen Details

| Screen | Elements | Valid | Issues |
|--------|----------|-------|--------|
`;

  for (const screen of results.screens) {
    const status = screen.issues.length === 0 ? '✅' : '⚠️';
    report += `| ${status} ${screen.screen} | ${screen.totalElements} | ${screen.validElements} | ${screen.issues.length} |\n`;
  }

  if (results.issues.length > 0) {
    report += `\n## Issues Found

| Screen | Line | Type | Issue |
|--------|------|------|-------|
`;
    for (const issue of results.issues) {
      report += `| ${issue.screen} | ${issue.lineNumber} | ${issue.type} | ${issue.issue} |\n`;
    }
  }

  report += `\n---

*Generated by validate-navigation.js*
`;

  return report;
}

/**
 * 生成修復建議
 */
function generateFixSuggestions(results) {
  if (results.issues.length === 0) {
    console.log('\n✅ No issues to fix!\n');
    return;
  }

  console.log('\n📝 Fix Suggestions\n');
  console.log('─'.repeat(60) + '\n');

  for (const issue of results.issues) {
    console.log(`File: ${issue.screen}`);
    console.log(`Line: ${issue.lineNumber}`);
    console.log(`Issue: ${issue.issue}`);

    // 根據問題類型提供建議
    switch (issue.type) {
      case 'empty-href':
        console.log('Fix: Replace href="#" with onclick="location.href=\'target.html\'"');
        break;
      case 'empty-onclick':
        console.log('Fix: Add navigation handler, e.g., onclick="location.href=\'target.html\'"');
        break;
      case 'close-button-no-onclick':
      case 'close-icon-no-onclick':
        console.log('🚨 Fix: This is a CLOSE/EXIT button - MUST have navigation!');
        console.log('   Add: onclick="location.href=\'previous-screen.html\'"');
        console.log('   Or:  onclick="history.back()"');
        console.log('   Example: onclick="location.href=\'SCR-TRAIN-001-select.html\'"');
        break;
      case 'settings-row-no-onclick':
        const prediction = predictTargetScreen(issue.textContent || '', issue.screen);
        console.log(`🚨 Fix: Settings row "${issue.textContent || '(unknown)'}" - MUST have onclick!`);
        console.log('   Option 1 (建立目標畫面):');
        console.log(`     onclick="location.href='${prediction.screenId}'"`);
        console.log('   Option 2 (使用 alert 說明功能):');
        console.log(`     onclick="alert('${prediction.description}')"`);
        console.log('   ⚠️ NEVER leave a settings row without onclick!');
        break;
      case 'clickable-row-no-onclick':
        console.log('⚠️ Fix: This row has clickable styling but no onclick handler');
        console.log('   Add: onclick="location.href=\'target.html\'"');
        console.log('   Or:  onclick="alert(\'功能說明\')"');
        break;
      case 'button-no-onclick':
        console.log('Fix: Add onclick handler to button, e.g., onclick="location.href=\'target.html\'"');
        break;
      case 'void-onclick-navigation':
        const voidPrediction = predictTargetScreen(issue.textContent || '', issue.screen);
        console.log(`🚨 Fix: Navigation button [${issue.elementId || '(unknown)'}] uses void(0) placeholder!`);
        console.log(`   Button text: "${issue.textContent || '(unknown)'}"`);
        console.log('   Option 1 (Create target screen):');
        console.log(`     onclick="location.href='${voidPrediction.screenId}'"`);
        console.log('   Option 2 (Navigate to existing screen):');
        console.log(`     onclick="location.href='SCR-MODULE-XXX-name.html'"`);
        console.log('   ⚠️ void(0) is NOT acceptable for navigation buttons!');
        break;
      case 'onclick-href':
      case 'href':
        console.log(`Fix: Create missing file or update target path`);
        console.log(`     Missing: ${issue.target}`);
        break;
      case 'missing-notify-parent':
        console.log('🔄 Fix: Add notify-parent.js for sidebar sync');
        console.log('   Add before </body>:');
        console.log('   <script src="../shared/notify-parent.js"></script>');
        break;
      case 'missing-postmessage-listener':
        console.log('🚨 Fix: Add postMessage listener to device-preview.html');
        console.log('   Add in <script> section:');
        console.log('   window.addEventListener(\'message\', function(event) {');
        console.log('     if (event.data && event.data.type === \'pageLoaded\') {');
        console.log('       syncSidebarFromIframe(event.data.url || event.data.pathname);');
        console.log('     }');
        console.log('   });');
        break;
    }
    console.log('');
  }
}

// Main execution
const args = process.argv.slice(2);
const showFix = args.includes('--fix');
const showReport = args.includes('--report');

const baseDir = process.cwd();
const results_data = validateNavigation(baseDir);

if (showFix) {
  generateFixSuggestions(results_data);
}

if (showReport) {
  const report = generateReport(results_data);
  const reportPath = path.join(baseDir, 'NAVIGATION-VALIDATION-REPORT.md');
  fs.writeFileSync(reportPath, report);
  console.log(`\n📄 Report saved to: ${reportPath}\n`);
}

// Exit with error code if issues found
process.exit(results_data.invalidElements > 0 ? 1 : 0);
