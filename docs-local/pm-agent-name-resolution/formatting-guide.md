# Formatting Guide: How to Reference Agents in PM_INSTRUCTIONS.md

**Date**: 2026-03-05
**Branch**: agenttype-enums
**Status**: Research complete

---

## 1. The Golden Rule

**Every agent reference that could become a `subagent_type` value MUST use the exact `name:` frontmatter field value from the agent's `.md` file.**

---

## 2. Formatting Patterns Analysis

### 2.1 Pattern Analysis Matrix

| Pattern | Example | Model Extraction | Risk Level | Recommendation |
|---------|---------|-----------------|------------|----------------|
| **(a)** Bold filename stem | `**local-ops**` | Model extracts "local-ops", may or may not convert to "Local Ops" | HIGH | DO NOT USE for delegation targets |
| **(b)** Bold name: field | `**Local Ops**` | Model extracts "Local Ops" directly -- exact match | LOW | RECOMMENDED for delegation targets |
| **(c)** Backtick/code | `` `Local Ops` `` | Model extracts "Local Ops" as code-like identifier | LOW | OK for delegation targets, suggests exactness |
| **(d)** Quoted | `"Local Ops"` | Model extracts "Local Ops" as string literal | LOW | OK in YAML examples |
| **(e)** Plain text | `Local Ops` | Model extracts "Local Ops" but may treat as prose | MEDIUM | Acceptable, but less emphasis than bold |
| **(f)** Bold with suffix | `**Local Ops** agent` | Model extracts "Local Ops" (strips "agent" naturally) | LOW | RECOMMENDED for prose readability |
| **(g)** Table cell bold | `\| **Local Ops** \|` | Model extracts "Local Ops" from table context | LOW | RECOMMENDED for tables |
| **(h)** YAML value | `agent: "Local Ops"` | Model extracts "Local Ops" as YAML value -- exact match | LOWEST | REQUIRED for YAML/code examples |

### 2.2 Detailed Analysis

#### (a) Bold filename stem: `**local-ops**`

**Current usage in PM_INSTRUCTIONS.md**: Extensive (18+ occurrences of `local-ops`)

**Problem**: The model sees "local-ops" and must decide whether to:
1. Pass it literally as `subagent_type="local-ops"` (FAILS)
2. Convert it to "Local Ops" (WORKS, but inference is unreliable)

**Evidence**: The implementation plan documents that `Agent(subagent_type="golang-engineer")` fails while `Agent(subagent_type="Golang Engineer")` succeeds. The model does NOT reliably perform stem-to-name conversion.

**Verdict**: DO NOT USE. This format directly causes delegation failures.

#### (b) Bold name: field: `**Local Ops**`

**Example**: `Delegate to **Local Ops**`

**Why it works**: The model extracts "Local Ops" as-is. This exactly matches `name: Local Ops` in `local-ops.md`. No conversion needed.

**Risk**: Minimal. The bold formatting clearly marks it as a proper noun/identifier.

**Edge case**: If the `name:` field contains underscores (`ticketing_agent`), bold formatting still works: `**ticketing_agent**`. The model will extract "ticketing_agent" literally.

**Verdict**: RECOMMENDED for all delegation targets in prose.

#### (c) Backtick/code: `` `Local Ops` ``

**Example**: `` Delegate to `Local Ops` ``

**Why it works**: Backticks signal "this is a literal value, use exactly as shown." The model is trained to treat backtick-enclosed values as exact identifiers.

**Advantage over bold**: Stronger signal that the value is an exact identifier, not prose.

**Best for**: Agent references in technical context, parenthetical identifiers, or where exactness is critical.

**Verdict**: GOOD for technical contexts. Useful in parenthetical identifiers: `**Ops** (\`Local Ops\`)`.

#### (d) Quoted: `"Local Ops"`

**Example**: `agent: "Local Ops"`

**Why it works**: Quotes explicitly mark the value as a string literal. Common in YAML/JSON examples.

**Best for**: YAML examples, code blocks, configuration snippets.

**Verdict**: REQUIRED for YAML/code examples. Acceptable but unnecessary in prose.

#### (e) Plain text: `Local Ops`

**Example**: `Delegate work to Local Ops for deployment.`

**Problem**: Without formatting, "Local Ops" may be interpreted as generic prose rather than a specific agent identifier. The model might not extract it precisely.

**Risk**: Medium. For well-known agents like "Research" or "Engineer" (single words), this is fine. For multi-word names like "Google Cloud Ops" or "Clerk Operations", lack of formatting creates ambiguity.

**Verdict**: Acceptable for well-known single-word agents. Use bold or backticks for multi-word names.

#### (f) Bold with suffix: `**Local Ops** agent`

**Example**: `Delegate to **Local Ops** agent for local development operations.`

**Why it works**: Bold marks the identifier; "agent" is clearly a descriptor, not part of the identifier. The model naturally strips "agent" when extracting the identifier.

**Risk**: Very low. The model understands that `**X** agent` means the agent named "X".

**Caution**: Do NOT say `**Local Ops Agent**` (capitalizing "Agent" as if part of the name), because `name:` is "Local Ops", not "Local Ops Agent".

**Verdict**: RECOMMENDED for prose readability. Natural English while preserving exact identifier.

#### (g) Table cell: `| **Local Ops** | Local development |`

**Example** (from current PM_INSTRUCTIONS.md):
```
| localhost, PM2, npm | **Local Ops** | Local development |
```

**Why it works**: Table cells clearly delimit the agent name. Bold within the cell adds emphasis.

**Risk**: Low. Tables are a natural way to present structured agent routing information.

**Verdict**: RECOMMENDED for routing tables and delegation matrices.

#### (h) YAML value: `agent: "Local Ops"`

**Example** (from current PM_INSTRUCTIONS.md):
```yaml
Task:
  agent: "Local Ops"
  task: "Start dev server"
```

**Why it works**: YAML values are the most explicit format. The model will extract the exact string value.

**Risk**: Lowest of all formats. The YAML structure makes the value unambiguous.

**Verdict**: REQUIRED for all YAML/code examples showing delegation.

---

## 3. Special Cases and Edge Cases

### 3.1 Agents with Non-Standard `name:` Values

Several agents have `name:` values that don't follow the "Title Case" convention:

| Agent File | `name:` Value | Format Issue | How to Reference |
|-----------|--------------|-------------|-----------------|
| `ticketing.md` | `ticketing_agent` | Underscores, lowercase | `**ticketing_agent**` (exact) |
| `aws-ops.md` | `aws_ops_agent` | Underscores, lowercase | `**aws_ops_agent**` (exact) |
| `nestjs-engineer.md` | `nestjs-engineer` | Hyphenated, lowercase | `**nestjs-engineer**` (exact) |
| `real-user.md` | `real-user` | Hyphenated, lowercase | `**real-user**` (exact) |
| `mpm-agent-manager.md` | `mpm_agent_manager` | Underscores, lowercase | `**mpm_agent_manager**` (exact) |
| `mpm-skills-manager.md` | `mpm_skills_manager` | Underscores, lowercase | `**mpm_skills_manager**` (exact) |

**Rule**: Always use the EXACT `name:` field value, even if it looks inconsistent with other agent names. The matching is exact, not normalized.

### 3.2 Agents with " Agent" in `name:` Field

| Agent File | `name:` Value | Note |
|-----------|--------------|------|
| `documentation.md` | `Documentation Agent` | Includes " Agent" suffix |
| `tmux-agent.md` | `Tmux Agent` | Includes " Agent" suffix |

**Rule**: Reference these as `**Documentation Agent**` and `**Tmux Agent**` -- the " Agent" IS part of the `name:` field.

**Caution**: The Agent Capabilities Generator strips " Agent" from display names (`clean_name = agent["name"].replace(" Agent", "")`). This means the generated capabilities section shows "Documentation" but the actual `name:` field is "Documentation Agent". This is a source of confusion.

### 3.3 Ambiguous Single-Word Names

Agents like `Research`, `Engineer`, `QA`, `Security`, `Ops` have single-word `name:` values. In prose, these could be confused with generic descriptions:

```
# Ambiguous:
"The research shows that..."  (is "research" a verb or an agent name?)
"The engineer should..."      (is "engineer" a person or an agent?)

# Clear:
"Delegate to **Research** for..."
"Delegate to **Engineer** for..."
```

**Rule**: Always bold single-word agent names when used as delegation targets.

---

## 4. Context-Dependent Formatting

### 4.1 Delegation Targets (MUST be exact)

Any text that the model will use to determine the `subagent_type` value:

```markdown
# CORRECT:
- Delegate to **Local Ops**
- Use the **Web QA** agent for browser testing
- PM delegates to **ticketing_agent**

# INCORRECT:
- Delegate to **local-ops**
- Use the **web-qa** agent
- PM delegates to **ticketing**
```

### 4.2 Descriptive Text (should be consistent but less critical)

Text describing agent capabilities where the model won't extract a delegation target:

```markdown
# ACCEPTABLE (consistency preferred):
"Local Ops handles local development operations"
"The Research agent investigates codebase patterns"
```

### 4.3 YAML/Code Examples (MUST be exact)

```yaml
# CORRECT:
agent: "Local Ops"
agent: "Web QA"
agent: "ticketing_agent"

# INCORRECT:
agent: "local-ops"
agent: "web-qa-agent"
agent: "ticketing-agent"
```

### 4.4 Tables (SHOULD be exact)

```markdown
# CORRECT:
| **Local Ops** | Local development |
| **Web QA** | Browser testing |
| **ticketing_agent** | Ticket operations |

# INCORRECT:
| **local-ops** | Local development |
| **web-qa-agent** | Browser testing |
```

---

## 5. Recommended Style Guide

### 5.1 For PM_INSTRUCTIONS.md Authors

1. **Always check the `name:` field** before referencing an agent. Use:
   ```bash
   grep '^name:' .claude/agents/<filename>.md
   ```

2. **Use bold for delegation targets in prose**:
   ```markdown
   Delegate to **Local Ops** for local development operations.
   ```

3. **Use quoted strings in YAML examples**:
   ```yaml
   agent: "Local Ops"
   ```

4. **Use backticks for parenthetical identifiers**:
   ```markdown
   **Ops** (`Local Ops`, `Vercel Ops`, `Google Cloud Ops`)
   ```

5. **Add "agent" suffix for readability** (lowercase, outside the bold):
   ```markdown
   The **Local Ops** agent handles server management.
   ```

6. **For non-standard names, use exactly as-is**:
   ```markdown
   Delegate to **ticketing_agent** for all ticket operations.
   Delegate to **aws_ops_agent** for AWS infrastructure.
   ```

### 5.2 Validation Checklist

Before committing PM_INSTRUCTIONS.md changes:

```bash
# Extract all bold agent references
grep -oP '\*\*[^*]+\*\*' src/claude_mpm/agents/PM_INSTRUCTIONS.md | sort -u

# Compare against actual name: fields
for f in .claude/agents/*.md; do
  grep '^name:' "$f" | sed 's/name: *//'
done | sort -u

# Any bold reference that doesn't appear in name: fields is a potential error
```

---

## 6. Summary of Best Practices

| Context | Format | Example |
|---------|--------|---------|
| Prose delegation instruction | Bold exact name | `Delegate to **Local Ops**` |
| YAML/code example | Quoted exact name | `agent: "Local Ops"` |
| Table cell | Bold exact name | `\| **Local Ops** \|` |
| Parenthetical identifier | Backtick exact name | `(\`Local Ops\`)` |
| Prose with suffix | Bold name + lowercase suffix | `**Local Ops** agent` |
| Non-standard names | Bold, exact as-is | `**ticketing_agent**` |
| Single-word names | Bold to distinguish from prose | `**Research**`, `**Engineer**` |
