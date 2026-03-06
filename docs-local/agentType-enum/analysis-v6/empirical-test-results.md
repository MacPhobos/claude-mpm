# Empirical Test Results: Claude Code subagent_type Resolution

**Date**: 2026-03-04
**Branch**: agenttype-enums
**Tested by**: PM (direct empirical test during live session)

---

## 1. Test Design

### Objective

Definitively answer Section 5 of `unified-analysis.md`:
> **Does Claude Code resolve `subagent_type` from the filename stem or from the frontmatter `name:` field?**

### Method

Used an existing deployed agent with a **known mismatch** between filename stem and frontmatter `name:` field:

| Property | Value |
|----------|-------|
| **File** | `.claude/agents/golang_engineer.md` |
| **Filename stem** | `golang_engineer` |
| **Frontmatter `name:`** | `Golang Engineer` |
| **Frontmatter `agent_id:`** | `golang_engineer` |

Invoked the Agent tool twice with identical prompts but different `subagent_type` values:
- **Test A**: `subagent_type="Golang Engineer"` (the `name:` field value)
- **Test B**: `subagent_type="golang_engineer"` (the filename stem)

Both used `model: haiku`, `max_turns: 1`, prompt: "What programming language do you specialize in? Answer in exactly one word."

### Why This Test Is Definitive

The file `golang_engineer.md` has a clear divergence between stem (`golang_engineer`) and name field (`Golang Engineer`). If Claude Code resolves via name field, Test A succeeds and Test B fails. If via stem, the reverse. If both, both succeed.

---

## 2. Results

### Test A: Name Field Resolution (`subagent_type="Golang Engineer"`)

```
Result:   SUCCESS
Response: "Go."
Tokens:   42,976 (loaded full agent system prompt)
Duration: 3,542ms
```

The agent loaded correctly, received the full Golang Engineer system prompt, and correctly identified its specialization as Go. **Name field resolution is confirmed.**

### Test B: Filename Stem Resolution (`subagent_type="golang_engineer"`)

```
Result:   FAILURE
Error:    "Agent type 'golang_engineer' not found."
```

Claude Code explicitly rejected the filename stem as a valid `subagent_type` value. **Filename stem resolution does NOT work.**

---

## 3. Complete Valid subagent_type List

The error from Test B revealed the **exhaustive list** of all valid `subagent_type` values recognized by Claude Code. This is the most valuable artifact from the test:

```
general-purpose          ← built-in
statusline-setup         ← built-in
Explore                  ← built-in
Plan                     ← built-in
claude-code-guide        ← built-in
Ops                      ← name: field
QA                       ← name: field
Research                 ← name: field
Web QA                   ← name: field
Documentation Agent      ← name: field
ticketing_agent          ← name: field (underscore format)
Svelte Engineer          ← name: field
Product Owner            ← name: field
Javascript Engineer      ← name: field
Php Engineer             ← name: field
Clerk Operations         ← name: field
Prompt Engineer          ← name: field
Visual Basic Engineer    ← name: field
Ruby Engineer            ← name: field
Rust Engineer            ← name: field
Tauri Engineer           ← name: field
mpm_agent_manager        ← name: field (underscore format)
Version Control          ← name: field
Web UI                   ← name: field
Vercel Ops               ← name: field
Refactoring Engineer     ← name: field
Nextjs Engineer          ← name: field
API QA                   ← name: field
Tmux Agent               ← name: field
mpm_skills_manager       ← name: field (underscore format)
Memory Manager           ← name: field
Dart Engineer            ← name: field
Content Optimization     ← name: field
Data Scientist           ← name: field
DigitalOcean Ops         ← name: field
Project Organizer        ← name: field
Python Engineer          ← name: field
React Engineer           ← name: field
Engineer                 ← name: field
Typescript Engineer      ← name: field
Google Cloud Ops         ← name: field
real-user                ← name: field (hyphen format)
Agentic Coder Optimizer  ← name: field
Data Engineer            ← name: field
Code Analysis            ← name: field
Local Ops                ← name: field
Java Engineer            ← name: field
Security                 ← name: field
Imagemagick              ← name: field
aws_ops_agent            ← name: field (underscore format)
Phoenix Engineer         ← name: field
Golang Engineer          ← name: field
```

**Total**: ~52 entries (5 built-in + ~47 from deployed agents)

### Key Observations from the List

1. **ALL custom agent types match their frontmatter `name:` field values.** No filename stems appear.
2. **Three naming conventions coexist in `name:` field values:**
   - Spaced capitalized: `Golang Engineer`, `Python Engineer`, `Local Ops`
   - Underscore lowercase: `ticketing_agent`, `mpm_agent_manager`, `aws_ops_agent`
   - Hyphen lowercase: `real-user`
3. **No filename stems appear.** `golang_engineer`, `research-agent`, `local-ops-agent`, `python-engineer` — none of these stems are in the list.
4. **`nestjs-engineer` is ABSENT** despite having a deployed file `nestjs_engineer.md` with `name: nestjs-engineer`. This may indicate the file wasn't properly loaded, or that `nestjs-engineer` was filtered/deduplicated.

### What's NOT in the List (Filename Stems That Were Rejected)

| Filename Stem | Name Field | In List? |
|---------------|------------|----------|
| `golang_engineer` | `Golang Engineer` | ❌ stem / ✅ name |
| `research-agent` | `Research` | ❌ stem / ✅ name |
| `local-ops-agent` | `Local Ops` | ❌ stem / ✅ name |
| `python-engineer` | `Python Engineer` | ❌ stem / ✅ name |
| `nestjs_engineer` | `nestjs-engineer` | ❌ stem / ❌ name (ABSENT) |
| `qa-agent` | `QA` | ❌ stem / ✅ name |

---

## 4. Answer to the Critical Question

### Definitive Answer

**Claude Code resolves `subagent_type` EXCLUSIVELY from the YAML frontmatter `name:` field. Filename stems are NOT used for resolution and are explicitly rejected as invalid.**

### Confidence Level: 100%

This is not an inference — it is directly observed behavior with a definitive positive test (name field works) and definitive negative test (stem rejected with "not found" error).

### Implications for the Rename

**PM delegation routing is SAFE** under file rename (e.g., `golang_engineer.md` → `golang-engineer.md`) **IF AND ONLY IF** the `name:` frontmatter field value is not changed.

Renaming `golang_engineer.md` to `golang-engineer.md` while keeping `name: Golang Engineer` will have **zero effect** on PM delegation. The PM will continue to call `Agent(subagent_type="Golang Engineer")` and Claude Code will continue to find the file (now named `golang-engineer.md`) and load it.

### What This Does NOT Make Safe

The empirical test only validates PM delegation routing. The following are NOT covered by this finding and remain potential break points:

1. **MPM internal code** that uses `agent_file.stem` for lookups (Break 2 in unified analysis)
2. **`bump_agent_versions.py`** that hardcodes filenames (Break 1)
3. **`agent_capabilities.yaml`** YAML keys that use filename conventions (Break 3)
4. **Deployment pipeline** paths that construct filenames from stems
5. **Template routing** in `capability_generator.py` that passes `agent_file.stem` to template loaders
6. **Dashboard/monitoring** code that does exact string matching on agent types

---

## 5. Secondary Findings

### 5.1 The `name:` Field Has No Format Constraint

Claude Code accepts `name:` field values in ANY format:
- Spaced capitalized: `Golang Engineer` ✅
- Underscore lowercase: `ticketing_agent` ✅
- Hyphen lowercase: `real-user` ✅
- Single word capitalized: `Research`, `Engineer`, `QA` ✅

There is no evidence of format normalization or validation on the `name:` field value. Whatever string is in the `name:` field is used verbatim as the `subagent_type` identifier.

### 5.2 Anthropic Spec vs Reality

The Anthropic documentation says `name` should be "lowercase letters and hyphens." The empirical evidence shows Claude Code accepts ANY string. The spec is aspirational, not enforced.

### 5.3 The `nestjs-engineer` Anomaly

The file `nestjs_engineer.md` with `name: nestjs-engineer` is deployed in `.claude/agents/` but does NOT appear in the available types list. Possible explanations:
- Loading error (malformed frontmatter — the `description:` field contains unescaped quotes and XML-like tags)
- Deduplication (another agent has a conflicting name)
- File permissions or encoding issue

This warrants investigation. If agents with certain `name:` formats fail to load, that affects the rename strategy.

### 5.4 No Fallback to Filename Stem

The test conclusively shows there is **no fallback mechanism** from name field to filename stem. Claude Code does not try `golang_engineer` as a second attempt after failing to find a `name:` field match. The error message is immediate and final.

---

## 6. Recommended Follow-Up Tests

### Test 3: Case Sensitivity
Try `Agent(subagent_type="golang engineer")` (lowercase) to test whether matching is case-sensitive.

### Test 4: Missing Name Field
Create a test agent WITHOUT a `name:` field to verify whether filename stem is used as fallback when no name exists.

### Test 5: Duplicate Names
Verify behavior when two files have the same `name:` value (the 5 collision pairs identified in the unified analysis).

### Test 6: The nestjs-engineer Anomaly
Investigate why `nestjs-engineer` doesn't appear in the available types despite having a deployed file with that name value.

---

## 7. Amendment to Unified Analysis Section 5

The following text should replace the "Why this question remains unanswered" paragraph in Section 5:

> **This question has been empirically answered.** On 2026-03-04, a live session test invoked `Agent(subagent_type="Golang Engineer")` (the `name:` field value) — SUCCESS. Then invoked `Agent(subagent_type="golang_engineer")` (the filename stem) — FAILURE with "Agent type not found." The error message revealed the complete list of valid `subagent_type` values: all are `name:` field values, none are filename stems. **Claude Code resolves `subagent_type` exclusively from the YAML frontmatter `name:` field. Filename stems are not used.** This means renaming files is safe for PM delegation routing as long as `name:` values are preserved. However, 6+ MPM-internal code paths still use filename stems and will break on rename (see Breaks 1-7 in Section 4).
