# claude-brain

A cross-project persistent knowledge system for Claude Code. Solves the problem of knowledge loss between sessions and knowledge isolation between projects.

## The Problem

AI conversations vanish between sessions. Knowledge learned in one project is invisible when working in another. Manual note-taking requires recognizing what matters at the time — which fails for insights that only become important in hindsight.

## The Solution: Three Layers

1. **Brain** — Curated, deliberate knowledge (decisions, patterns, bug fixes). YAML index + markdown entries. Captures *spec lineage*: what was decided and why.

2. **Transcript Archive** — Verbatim session storage. Captures *implementation lineage*: small choices, dead ends, mid-flight insights. Zero-effort capture via scheduled task.

3. **SessionStart Hook** — Bridges sessions by auto-injecting recent transcript context. No behavior change required from the user.

## Architecture

```
data/brain/
  index.yaml              — Searchable index (O(1) discovery)
  entries/                 — One markdown file per entry
  summaries/              — Per-project rollup summaries

data/transcripts/
  {project-slug}/          — Archived sessions by project
  index.json              — Dedup tracking (file hashes)

scripts/
  archive_transcripts.py  — Daily scheduled task for transcript capture
```

## Brain Entry Schema

```yaml
---
id: YYYY-MM-DD-slug
date: YYYY-MM-DD
type: insight | decision | pattern | bug-fix | anti-pattern | reference
project: project-slug
related_projects: [slug1, slug2]
tags: [searchable, tags]
related: [other-entry-id]
---

# Title

## Context
What situation triggered this knowledge.

## Solution / Insight / Decision
The core content.

## Key Lesson
The generalizable takeaway.

## Applies To
When to recall this entry.
```

## Entry Types

| Type | When to Use |
|------|-------------|
| `decision` | Architectural choices, technology selections, approach commitments |
| `pattern` | Reusable solutions, successful approaches, techniques |
| `insight` | Non-obvious learnings, "aha" moments, things that surprised you |
| `bug-fix` | Solutions to specific problems (for when they recur) |
| `anti-pattern` | Approaches that failed — what NOT to do |
| `reference` | Pointers to external systems, URLs, resources |

## Index-First Search

The `index.yaml` file enables O(1) discovery:
- Search by `tags`, `project`, `type`, or `related_projects`
- Read the one-line `summary` to decide relevance
- Only read the full entry file when needed

This beats scanning N files and keeps context windows lean.

## Setup

1. Create `data/brain/index.yaml` with the schema above
2. Configure `archive_transcripts.py` with your project directory mappings
3. Schedule the archive script to run daily (e.g., 5:45 AM)
4. Add a SessionStart hook to inject recent transcript context

## Integration with Claude Code

The system integrates via:
- **Global CLAUDE.md** — instructs Claude to read the brain index when context is needed
- **Slash commands** — `/learn` (create entry), `/recall` (search), `/capture` (quick inbox)
- **Scheduled tasks** — daily transcript archival
- **SessionStart hooks** — auto-inject recent context

## License

MIT
