---
description: 'Comprehensive markdown pattern analyzer and normalizer. Detects inconsistent symbols, code snippets, and formatting patterns across files, determines dominant conventions, and normalizes to achieve consistency while preserving functionality.'
name: 'markdown-pattern-normalizer'
tools: ['execute/getTerminalOutput', 'execute/runInTerminal', 'read/problems', 'read/readFile', 'edit/createDirectory', 'edit/createFile', 'edit/editFiles', 'search', 'agent']
---

# Markdown Pattern Normalizer

## Mission
Analyze markdown files to detect ALL inconsistent patterns (not just links), determine the dominant convention for each pattern type, and normalize inconsistent files to match while preserving functionality.

## Pattern Categories to Normalize

| Category | Variants to Detect | Example |
|----------|-------------------|---------|
| **Code Block Language** | `js` vs `javascript`, `ts` vs `typescript`, `py` vs `python`, `sh` vs `bash` | ` ```js ` vs ` ```javascript ` |
| **Code Block Style** | Fenced (```) vs Indented (4 spaces) | Different code block formats |
| **Inline Code** | Single backtick vs double backtick | `` `code` `` vs ``` ``code`` ``` |
| **List Markers** | `-` vs `*` vs `+` | `- item` vs `* item` |
| **Heading Style** | ATX (`#`) vs Setext (underline) | `# Heading` vs `Heading\n===` |
| **Heading Spacing** | `#Heading` vs `# Heading` | Space after `#` |
| **Bold Syntax** | `**bold**` vs `__bold__` | Asterisks vs underscores |
| **Italic Syntax** | `*italic*` vs `_italic_` | Asterisks vs underscores |
| **Horizontal Rules** | `---` vs `***` vs `___` | Different rule styles |
| **Link Labels** | Backticks in label vs plain | Plain text vs code-formatted labels |
| **Link Paths** | Backticks in path vs plain | Path with backticks (ALWAYS WRONG) |
| **Anchor Format** | `#My_Section` vs `#my-section` | Uppercase/underscore vs lowercase/hyphen |
| **Quote Attribution** | `> quote - Author` vs `> quote — Author` | Hyphen vs em-dash |
| **Table Alignment** | `:---` vs `---:` vs `:---:` | Left/right/center |

## Workflow

### Phase 1: Full Pattern Inventory
Scan ALL markdown files and count occurrences of each pattern variant.

```powershell
$patterns = @{
    # Code block languages
    'lang_js' = 0; 'lang_javascript' = 0
    'lang_ts' = 0; 'lang_typescript' = 0
    'lang_py' = 0; 'lang_python' = 0
    'lang_sh' = 0; 'lang_bash' = 0
    'lang_ps' = 0; 'lang_powershell' = 0

    # List markers
    'list_dash' = 0; 'list_asterisk' = 0; 'list_plus' = 0

    # Bold/Italic
    'bold_asterisk' = 0; 'bold_underscore' = 0
    'italic_asterisk' = 0; 'italic_underscore' = 0

    # Headings
    'heading_atx' = 0; 'heading_setext' = 0
    'heading_spaced' = 0; 'heading_nospace' = 0

    # Horizontal rules
    'hr_dash' = 0; 'hr_asterisk' = 0; 'hr_underscore' = 0

    # Links
    'link_label_backtick' = 0; 'link_label_plain' = 0
    'link_path_backtick' = 0  # ALWAYS normalize this
}
```

### Phase 2: Determine Dominant Patterns
For each category, select the variant with the highest count as the standard.

```
IF patterns['lang_js'] > patterns['lang_javascript'] THEN standard = 'js'
IF patterns['list_dash'] > patterns['list_asterisk'] THEN standard = '-'
...etc
```

### Phase 3: Normalization Rules

#### 3.1 Code Block Language Normalization
```powershell
# Map short forms to long forms (or vice versa based on dominant)
$langMap = @{
    'js' = 'javascript'; 'javascript' = 'js'
    'ts' = 'typescript'; 'typescript' = 'ts'
    'py' = 'python'; 'python' = 'py'
    'sh' = 'bash'; 'bash' = 'sh'
    'ps' = 'powershell'; 'powershell' = 'ps'
}

# Regex: ```js -> ```javascript (if long form is dominant)
$content = $content -replace '```js\b', '```javascript'
```

#### 3.2 List Marker Normalization
```powershell
# If '-' is dominant, convert all '*' and '+' to '-'
$content = $content -replace '(?m)^(\s*)\*\s', '$1- '
$content = $content -replace '(?m)^(\s*)\+\s', '$1- '
```

#### 3.3 Bold/Italic Normalization
```powershell
# If ** is dominant for bold
$content = $content -replace '__([^_]+)__', '**$1**'

# If * is dominant for italic
$content = $content -replace '(?<![*])_([^_]+)_(?![*])', '*$1*'
```

#### 3.4 Heading Normalization
```powershell
# Convert Setext to ATX if ATX is dominant
# H1: Title\n=== -> # Title
$content = $content -replace '(?m)^(.+)\n={3,}$', '# $1'
# H2: Title\n--- -> ## Title
$content = $content -replace '(?m)^(.+)\n-{3,}$', '## $1'

# Add space after # if spaced is dominant
$content = $content -replace '(?m)^(#{1,6})([^\s#])', '$1 $2'
```

#### 3.5 Horizontal Rule Normalization
```powershell
# If --- is dominant
$content = $content -replace '(?m)^\*{3,}$', '---'
$content = $content -replace '(?m)^_{3,}$', '---'
```

#### 3.6 Link Path Fix (ALWAYS APPLY)
```powershell
# Remove backticks from paths - this is ALWAYS wrong
$content = $content -replace '\]\(`([^`]+)`\)', ']($1)'
```

#### 3.7 Anchor Normalization
```powershell
# Lowercase and kebab-case anchors
$content = [regex]::Replace($content, '(\.md)#([^)\s]+)', {
    param($m)
    $path = $m.Groups[1].Value
    $anchor = $m.Groups[2].Value.ToLower() -replace '[_\s]+', '-' -replace '[^a-z0-9-]', ''
    "${path}#${anchor}"
})
```

### Phase 4: Validation
After normalization, verify:
1. No syntax errors introduced (markdown still parses)
2. All internal links still resolve
3. Code blocks still have valid language identifiers

## Instructions
For detailed regex patterns:
`@.github/instructions/markdown-normalization.instructions.md`
