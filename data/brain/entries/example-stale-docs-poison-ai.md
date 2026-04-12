---
id: example-stale-docs-poison-ai
date: 2026-03-28
type: insight
project: example-project
related_projects: [claude-brain]
tags: [documentation, ai-assisted-development, architecture]
---

# Stale Docs Cause AI to Generate Code for the Old Architecture

## Context
During a major rebuild, the AI assistant kept generating code patterns from the old architecture — vanilla JS patterns when the project had moved to a component-based framework. The AI was reading outdated documentation that described the old system.

## Solution / Insight / Decision
Triage documentation BEFORE starting any rebuild:
1. Mark docs as `current`, `historical`, or `delete`
2. Move historical docs to an archive folder the AI won't read by default
3. Update or create new docs that describe the target architecture
4. Add a note in CLAUDE.md: "Do not reference archived docs for new code"

## Key Lesson
AI assistants treat all accessible documentation as equally authoritative. Stale docs don't just waste context — they actively produce wrong output. Documentation hygiene is a prerequisite for AI-assisted development, not a nice-to-have.

## Applies To
- Any project rebuild or major refactor with AI assistance
- Projects with documentation older than the current architecture
- Onboarding AI to an existing codebase
