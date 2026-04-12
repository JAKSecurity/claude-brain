# claude-brain

## Project Overview
Cross-project persistent knowledge system for Claude Code. Three layers: curated Brain entries (decisions, patterns, insights), verbatim transcript archive (implementation lineage), and SessionStart hook (session bridging).

## Key Design Principles
- **Index-first search** — single YAML index for O(1) discovery, full entries on demand
- **Spec vs implementation lineage** — Brain captures deliberate knowledge; transcripts capture everything else
- **Zero-effort capture** — scheduled task archives transcripts automatically; no user behavior change needed
- **Cross-project visibility** — entries can reference multiple projects via `related_projects`

## Directory Structure
- `data/brain/index.yaml` — searchable index
- `data/brain/entries/` — one markdown file per brain entry
- `data/brain/summaries/` — per-project rollup summaries
- `data/transcripts/` — archived sessions by project slug
- `scripts/archive_transcripts.py` — daily transcript capture script
- `docs/KNOWLEDGE_SYSTEM.md` — full system documentation

## Brain Entry Types
- `decision` — architectural choices, approach commitments
- `pattern` — reusable solutions, successful techniques
- `insight` — non-obvious learnings
- `bug-fix` — solutions to recurring problems
- `anti-pattern` — approaches that failed
- `reference` — pointers to external resources

## Scripts
- `scripts/archive_transcripts.py` — reads Claude Code JSONL transcripts from `~/.claude/projects/`, converts to markdown, writes to `data/transcripts/`. Uses PROJECT_MAP dict for slug resolution. Stdlib only (no external deps).
