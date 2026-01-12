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

# End Arcana Skills
