/**
 * Mermaid Flow Diagram Generator
 *
 * 從 generated-ui 目錄產生 Mermaid flowchart 格式的流程圖
 * 可嵌入 SDD 文件使用
 *
 * Usage:
 *   node generate-mermaid-flow.js <generated-ui-path> [output-path]
 *
 * Example:
 *   node generate-mermaid-flow.js ./generated-ui ./docs/flow-diagram.md
 */

const fs = require('fs');
const path = require('path');

// 模組中文名稱對照
const MODULE_NAMES = {
  'AUTH': '認證模組',
  'ONBOARD': '新手引導',
  'DASH': '首頁',
  'TRAIN': '訓練模組',
  'REWARD': '獎勵模組',
  'REPORT': '報表模組',
  'DEVICE': '裝置模組',
  'SETTING': '設定模組',
  'COM': '共用元件'
};

// 模組圖示
const MODULE_ICONS = {
  'AUTH': '🔐',
  'ONBOARD': '📚',
  'DASH': '🏠',
  'TRAIN': '🎮',
  'REWARD': '🏆',
  'REPORT': '📊',
  'DEVICE': '📱',
  'SETTING': '⚙️',
  'COM': '🧩'
};

/**
 * 掃描 HTML 檔案並解析 Button Navigation
 */
function scanHtmlFiles(basePath) {
  const screens = [];
  const navigations = [];

  // 遞迴掃描目錄
  function scanDir(dirPath) {
    if (!fs.existsSync(dirPath)) return;

    const items = fs.readdirSync(dirPath);
    for (const item of items) {
      const fullPath = path.join(dirPath, item);
      const stat = fs.statSync(fullPath);

      if (stat.isDirectory() && !['shared', 'docs', 'screenshots', 'assets', 'node_modules'].includes(item)) {
        scanDir(fullPath);
      } else if (item.endsWith('.html') && !['index.html', 'nav.html', 'device-preview.html'].includes(item)) {
        const screenInfo = parseHtmlFile(fullPath, basePath);
        if (screenInfo) {
          screens.push(screenInfo);
          navigations.push(...screenInfo.navigations);
        }
      }
    }
  }

  scanDir(basePath);
  return { screens, navigations };
}

/**
 * 解析單一 HTML 檔案
 */
function parseHtmlFile(filePath, basePath) {
  const content = fs.readFileSync(filePath, 'utf8');
  const fileName = path.basename(filePath, '.html');
  const relativePath = path.relative(basePath, filePath);

  // 從檔名解析畫面 ID
  // 支援格式: SCR-AUTH-001-login.html 或 AUTH-001-login.html
  let screenId = fileName;
  let module = '';
  let name = '';

  // 嘗試匹配 SCR-MODULE-NNN 或 MODULE-NNN 格式
  const scrMatch = fileName.match(/^(SCR-)?([A-Z]+)-(\d{3})(?:-(.+))?$/);
  if (scrMatch) {
    module = scrMatch[2];
    const seq = scrMatch[3];
    name = scrMatch[4] || '';
    screenId = `SCR-${module}-${seq}`;
  }

  // 從 HTML 中提取標題 (如果有)
  const titleMatch = content.match(/<title>([^<]+)<\/title>/i);
  const displayName = titleMatch ? titleMatch[1] : (name || screenId);

  // 解析 Button Navigation
  const navigations = [];

  // 匹配 onclick="location.href='...'"
  const onclickRegex = /onclick=["']location\.href=["']([^"']+)["']["']/g;
  let match;
  while ((match = onclickRegex.exec(content)) !== null) {
    const target = normalizeTarget(match[1], relativePath);
    if (target) {
      navigations.push({
        source: screenId,
        target: target,
        type: 'navigate',
        inferred: content.includes('data-inferred') && content.indexOf('data-inferred') < content.indexOf(match[0]) + 100
      });
    }
  }

  // 匹配 href="..."
  const hrefRegex = /<a[^>]+href=["']([^"'#]+\.html)["'][^>]*>/g;
  while ((match = hrefRegex.exec(content)) !== null) {
    const target = normalizeTarget(match[1], relativePath);
    if (target && target !== screenId) {
      navigations.push({
        source: screenId,
        target: target,
        type: 'link',
        inferred: false
      });
    }
  }

  return {
    id: screenId,
    module: module,
    name: displayName,
    path: relativePath,
    navigations: navigations
  };
}

/**
 * 標準化目標路徑為 Screen ID
 */
function normalizeTarget(href, sourcePath) {
  if (!href || href === '#' || href.startsWith('http') || href.startsWith('javascript')) {
    return null;
  }

  // 處理相對路徑
  const resolved = path.normalize(path.join(path.dirname(sourcePath), href));
  const fileName = path.basename(resolved, '.html');

  // 轉換為 SCR ID
  const match = fileName.match(/^(SCR-)?([A-Z]+)-(\d{3})/);
  if (match) {
    return `SCR-${match[2]}-${match[3]}`;
  }

  return null;
}

/**
 * 產生 Mermaid Flowchart
 */
function generateMermaidFlow(screens, navigations) {
  const lines = [];
  lines.push('```mermaid');
  lines.push('flowchart TB');
  lines.push('');

  // 按模組分組
  const moduleGroups = {};
  for (const screen of screens) {
    if (!screen.module) continue;
    if (!moduleGroups[screen.module]) {
      moduleGroups[screen.module] = [];
    }
    moduleGroups[screen.module].push(screen);
  }

  // 產生 subgraph
  for (const [module, moduleScreens] of Object.entries(moduleGroups)) {
    const icon = MODULE_ICONS[module] || '📄';
    const name = MODULE_NAMES[module] || module;

    lines.push(`    subgraph ${module}["${icon} ${name}"]`);
    lines.push('        direction TB');

    // 排序畫面 (按序號)
    moduleScreens.sort((a, b) => a.id.localeCompare(b.id));

    for (const screen of moduleScreens) {
      const label = screen.name.length > 20 ? screen.name.substring(0, 18) + '...' : screen.name;
      lines.push(`        ${screen.id.replace(/-/g, '_')}["${screen.id}<br/>${label}"]`);
    }

    lines.push('    end');
    lines.push('');
  }

  // 產生連線
  lines.push('    %% 畫面連線');

  // 去重複
  const uniqueNavs = new Map();
  for (const nav of navigations) {
    const key = `${nav.source}->${nav.target}`;
    if (!uniqueNavs.has(key)) {
      uniqueNavs.set(key, nav);
    }
  }

  for (const nav of uniqueNavs.values()) {
    const sourceId = nav.source.replace(/-/g, '_');
    const targetId = nav.target.replace(/-/g, '_');
    const arrow = nav.inferred ? '-.->' : '-->';
    const comment = nav.inferred ? ' %% 推斷' : '';
    lines.push(`    ${sourceId} ${arrow} ${targetId}${comment}`);
  }

  lines.push('```');

  return lines.join('\n');
}

/**
 * 產生摘要報告
 */
function generateSummary(screens, navigations) {
  const lines = [];
  lines.push('# UI Flow Diagram');
  lines.push('');
  lines.push('> 此檔案由 `generate-mermaid-flow.js` 自動產生');
  lines.push('> 可直接嵌入 SDD 文件使用');
  lines.push('');
  lines.push('## 統計');
  lines.push('');
  lines.push(`| 項目 | 數量 |`);
  lines.push(`|------|------|`);
  lines.push(`| 畫面總數 | ${screens.length} |`);
  lines.push(`| 導航連結 | ${navigations.length} |`);

  // 統計各模組
  const moduleCounts = {};
  for (const screen of screens) {
    if (screen.module) {
      moduleCounts[screen.module] = (moduleCounts[screen.module] || 0) + 1;
    }
  }

  lines.push('');
  lines.push('## 模組分佈');
  lines.push('');
  lines.push('| 模組 | 畫面數 |');
  lines.push('|------|--------|');
  for (const [module, count] of Object.entries(moduleCounts).sort()) {
    const name = MODULE_NAMES[module] || module;
    lines.push(`| ${name} (${module}) | ${count} |`);
  }

  // 統計推斷的導航
  const inferredNavs = navigations.filter(n => n.inferred);
  if (inferredNavs.length > 0) {
    lines.push('');
    lines.push('## 推斷的導航 (需人工確認)');
    lines.push('');
    lines.push('| 來源 | 目標 |');
    lines.push('|------|------|');
    for (const nav of inferredNavs) {
      lines.push(`| ${nav.source} | ${nav.target} |`);
    }
  }

  lines.push('');
  lines.push('## 流程圖');
  lines.push('');

  return lines.join('\n');
}

/**
 * 主程式
 */
function main() {
  const args = process.argv.slice(2);

  if (args.length < 1) {
    console.log('Usage: node generate-mermaid-flow.js <generated-ui-path> [output-path]');
    console.log('');
    console.log('Example:');
    console.log('  node generate-mermaid-flow.js ./generated-ui ./docs/flow-diagram.md');
    process.exit(1);
  }

  const basePath = args[0];
  const outputPath = args[1] || path.join(basePath, 'docs', 'flow-diagram.md');

  console.log(`Scanning: ${basePath}`);

  // 掃描檔案
  const { screens, navigations } = scanHtmlFiles(basePath);

  console.log(`Found ${screens.length} screens, ${navigations.length} navigations`);

  // 產生 Mermaid
  const summary = generateSummary(screens, navigations);
  const mermaid = generateMermaidFlow(screens, navigations);

  // 輸出
  const output = summary + mermaid;

  // 確保輸出目錄存在
  const outputDir = path.dirname(outputPath);
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  fs.writeFileSync(outputPath, output);
  console.log(`Generated: ${outputPath}`);

  // 同時輸出純 Mermaid (方便嵌入)
  const mermaidOnlyPath = outputPath.replace('.md', '.mermaid');
  fs.writeFileSync(mermaidOnlyPath, mermaid.replace('```mermaid\n', '').replace('\n```', ''));
  console.log(`Generated: ${mermaidOnlyPath}`);
}

main();
