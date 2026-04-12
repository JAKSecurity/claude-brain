---
id: example-index-first-search-pattern
date: 2026-03-17
type: pattern
project: claude-brain
tags: [architecture, search, context-management, yaml, performance]
---

# Single Index File for O(1) Knowledge Discovery

## Context
When building a persistent knowledge base for AI assistants, the retrieval mechanism determines whether the system gets used or ignored. Scanning every file in a directory (O(N)) wastes context window space and gets slower as entries accumulate.

## Solution / Insight / Decision
Use a single `index.yaml` file as the discovery layer:
- Each entry has: id, type, project, tags, one-line summary, file pointer
- Search by filtering the index (tags, project, type)
- Only read the full entry file when the summary confirms relevance

This is analogous to a database index — the overhead of maintaining it is low, and the query-time savings are enormous.

## Key Lesson
For AI knowledge bases, the cost of reading irrelevant content (context window pollution) is higher than the cost of maintaining an index. Design for read-heavy workloads.

## Applies To
- Any AI-persistent knowledge system
- File-based search across more than ~10 entries
- Cross-project knowledge graphs
