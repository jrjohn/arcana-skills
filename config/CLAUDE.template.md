# Arcana Skills Configuration

## File Size Management for Skills

### Rule: Split Large Markdown Files

When any `.md` file in `~/.claude/skills/` exceeds **80% of the AI read limit** (~20,000 tokens or ~2,200 lines), it MUST be split into smaller reference files.

### Detection

Before reading a large reference file, check its size:
```bash
wc -l <file_path>
```

If lines > 2,200 OR tokens > 20,000, the file needs restructuring.

### Split Strategy

1. **Create a main index file** (condensed, < 300 lines)
   - Quick reference tables
   - File index linking to split files
   - Checklists and summaries
   - No verbose code examples

2. **Split by category** into separate files:
   - By platform: `*-html.md`, `*-react.md`, `*-swiftui.md`, `*-compose.md`
   - By function: `*-components.md`, `*-templates.md`, `*-assets.md`
   - By topic: `*-navigation.md`, `*-forms.md`, `*-lists.md`

3. **Naming convention**:
   ```
   {original-name}.md          -> Main index (condensed)
   {original-name}-{split}.md  -> Split reference files
   ```

### When to Split

| Indicator | Action |
|-----------|--------|
| File read error (exceeds limit) | Split immediately |
| File > 2,000 lines | Split proactively |
| File > 15,000 tokens | Split proactively |
| Multiple distinct topics | Split by topic |
| Multiple platforms | Split by platform |

## Skill Development Guidelines

### Skill Structure

```
~/.claude/skills/{skill-name}/
├── CLAUDE.md              # Skill-specific instructions (optional)
├── instructions.md        # Main skill instructions
└── references/            # Reference files
    ├── {topic}.md         # Main index (< 300 lines)
    └── {topic}-{split}.md # Split files (< 500 lines each)
```

### Reference File Best Practices

1. **Keep files focused** - One topic per file
2. **Use tables** - Faster to scan than prose
3. **Minimize code blocks** - Only essential examples
4. **Cross-reference** - Link related files
5. **Version notes** - Track major changes

## IEC 62304 Workflow Enforcement

### MANDATORY: Skill Coordination Rules

When using `app-requirements-skill` for App development documentation:

| Phase | Action | MANDATORY |
|-------|--------|-----------|
| 需求收集開始 | 啟用 `app-uiux-designer.skill` 詢問 UI 需求 | **YES** |
| SDD 完成後 | 啟用 `app-uiux-designer.skill` 產生 UI Flow | **YES** |
| UI Flow 完成後 | 回補 SDD + SRS | **YES** |

### Forbidden Actions

- **禁止** 直接手動建立 UI Flow HTML（必須透過 app-uiux-designer.skill）
- **禁止** 跳過 UI 需求收集階段
- **禁止** SDD 完成後不產生 UI Flow

### Checklist Before Completing App Documentation

```
[ ] 需求收集時已詢問 UI 需求（平台、裝置、畫面數、模組、風格、色彩、深色模式）
[ ] SRS 完成
[ ] SDD 完成
[ ] 已啟用 app-uiux-designer.skill 產生：
    [ ] Design Token JSON
    [ ] Theme CSS
    [ ] HTML UI Flow
    [ ] Screenshots
[ ] SDD 已回補 UI 原型參考
[ ] SRS 已回補 Screen References + Inferred Requirements
[ ] RTM 追溯 100%
[ ] DOCX 已產生
```

# End Arcana Skills
