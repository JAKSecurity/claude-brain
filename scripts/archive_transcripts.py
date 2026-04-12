"""
Archive Claude Code session transcripts to a permanent, searchable location.

Scans all project transcript directories under ~/.claude/projects/,
converts JSONL transcripts to readable markdown, and stores them in
data/transcripts/ organized by project and date.

Designed to run as a scheduled task (daily) so it catches all sessions
regardless of how they ended — explicit close, abandoned, crashed, etc.

Usage:
    python scripts/archive_transcripts.py [--force] [--dry-run]

    --force   Re-archive all transcripts, not just new/modified ones
    --dry-run Show what would be archived without writing files
"""

import json
import os
import sys
import hashlib
from datetime import datetime, timezone
from pathlib import Path

# Paths
CLAUDE_PROJECTS = Path(os.path.expanduser("~/.claude/projects"))
ARCHIVE_DIR = Path(__file__).parent.parent / "data" / "transcripts"
ARCHIVE_INDEX = ARCHIVE_DIR / "index.json"

# Project slug mapping: directory name -> human-readable project slug
# Claude Code stores transcripts in directories named after the project path
# with path separators replaced by dashes. Map these to short slugs.
# Example: "C--Users-alice-projects-my-app" -> "my-app"
PROJECT_MAP = {
    # Add your project directory mappings here:
    # "C--Users-yourname-projects-my-project": "my-project",
}


def load_index():
    """Load the archive index tracking what's already been archived."""
    if ARCHIVE_INDEX.exists():
        with open(ARCHIVE_INDEX, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"archived": {}, "last_run": None}


def save_index(index):
    """Save the archive index."""
    ARCHIVE_INDEX.parent.mkdir(parents=True, exist_ok=True)
    index["last_run"] = datetime.now(timezone.utc).isoformat()
    with open(ARCHIVE_INDEX, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)


def file_hash(path):
    """Quick hash based on size + mtime for change detection."""
    stat = path.stat()
    return f"{stat.st_size}:{stat.st_mtime_ns}"


def parse_transcript(jsonl_path):
    """Parse a JSONL transcript into structured messages."""
    messages = []
    metadata = {
        "session_id": jsonl_path.stem,
        "project_dir": jsonl_path.parent.name,
        "file_size": jsonl_path.stat().st_size,
    }

    first_timestamp = None
    last_timestamp = None

    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            msg_type = obj.get("type", "")
            timestamp = obj.get("timestamp", "")

            if timestamp:
                if first_timestamp is None:
                    first_timestamp = timestamp
                last_timestamp = timestamp

            if msg_type in ("user", "assistant"):
                message = obj.get("message", {})
                role = message.get("role", msg_type)
                content = extract_content(message.get("content", ""))

                if content.strip():
                    messages.append({
                        "role": role,
                        "content": content,
                        "timestamp": timestamp,
                    })

            # Capture tool use for context
            elif msg_type == "tool_use":
                tool_name = obj.get("name", "unknown")
                messages.append({
                    "role": "tool",
                    "content": f"[Tool: {tool_name}]",
                    "timestamp": timestamp,
                })

    metadata["first_timestamp"] = first_timestamp
    metadata["last_timestamp"] = last_timestamp
    metadata["message_count"] = len(messages)

    return messages, metadata


def extract_content(content):
    """Extract text from content which may be a string or list of blocks."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    parts.append(block.get("text", ""))
                elif block.get("type") == "tool_use":
                    parts.append(f"[Tool: {block.get('name', 'unknown')}]")
                elif block.get("type") == "tool_result":
                    result_content = block.get("content", "")
                    if isinstance(result_content, str) and len(result_content) < 500:
                        parts.append(f"[Tool result: {result_content[:200]}]")
                    else:
                        parts.append("[Tool result]")
        return "\n".join(parts)
    return str(content)


def transcript_to_markdown(messages, metadata):
    """Convert parsed transcript to readable markdown."""
    project_slug = PROJECT_MAP.get(metadata["project_dir"], metadata["project_dir"])
    session_id = metadata["session_id"]

    # Parse timestamps for header
    start = metadata.get("first_timestamp", "unknown")
    end = metadata.get("last_timestamp", "unknown")

    try:
        start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
        start_str = start_dt.strftime("%Y-%m-%d %H:%M")
    except (ValueError, AttributeError):
        start_str = start

    try:
        end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
        end_str = end_dt.strftime("%Y-%m-%d %H:%M")
    except (ValueError, AttributeError):
        end_str = end

    lines = [
        f"# Session: {session_id[:8]}",
        f"",
        f"| Field | Value |",
        f"|-------|-------|",
        f"| Project | {project_slug} |",
        f"| Session ID | `{session_id}` |",
        f"| Started | {start_str} UTC |",
        f"| Ended | {end_str} UTC |",
        f"| Messages | {metadata['message_count']} |",
        f"| Raw size | {metadata['file_size']:,} bytes |",
        f"",
        f"---",
        f"",
    ]

    for msg in messages:
        role = msg["role"]
        content = msg["content"]

        if role == "user":
            # Truncate very long user messages (e.g., pasted files)
            if len(content) > 2000:
                content = content[:2000] + f"\n\n[... truncated, {len(content):,} chars total]"
            lines.append(f"## User\n\n{content}\n")
        elif role == "assistant":
            # Truncate very long assistant messages
            if len(content) > 5000:
                content = content[:5000] + f"\n\n[... truncated, {len(content):,} chars total]"
            lines.append(f"## Assistant\n\n{content}\n")
        elif role == "tool":
            lines.append(f"*{content}*\n")

    return "\n".join(lines)


def archive_transcript(jsonl_path, dry_run=False):
    """Archive a single transcript file. Returns (output_path, metadata) or None."""
    messages, metadata = parse_transcript(jsonl_path)

    if metadata["message_count"] < 2:
        return None  # Skip trivial sessions (e.g., just a health check)

    project_slug = PROJECT_MAP.get(metadata["project_dir"], metadata["project_dir"])

    # Determine date from first timestamp
    try:
        start_dt = datetime.fromisoformat(
            metadata["first_timestamp"].replace("Z", "+00:00")
        )
        date_str = start_dt.strftime("%Y-%m-%d")
        time_str = start_dt.strftime("%H%M")
    except (ValueError, AttributeError, TypeError):
        date_str = "unknown-date"
        time_str = "0000"

    # Output path: data/transcripts/{project}/{date}_{time}_{session_id_short}.md
    session_short = metadata["session_id"][:8]
    output_dir = ARCHIVE_DIR / project_slug
    output_file = output_dir / f"{date_str}_{time_str}_{session_short}.md"

    if dry_run:
        print(f"  Would archive: {output_file.name} ({metadata['message_count']} messages)")
        return str(output_file), metadata

    output_dir.mkdir(parents=True, exist_ok=True)
    md_content = transcript_to_markdown(messages, metadata)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(md_content)

    return str(output_file), metadata


def main():
    force = "--force" in sys.argv
    dry_run = "--dry-run" in sys.argv

    if not CLAUDE_PROJECTS.exists():
        print(f"No Claude projects directory found at {CLAUDE_PROJECTS}")
        sys.exit(1)

    index = load_index()
    archived = index["archived"]

    new_count = 0
    updated_count = 0
    skipped_count = 0
    trivial_count = 0

    for proj_dir in sorted(CLAUDE_PROJECTS.iterdir()):
        if not proj_dir.is_dir():
            continue

        project_name = PROJECT_MAP.get(proj_dir.name, proj_dir.name)
        jsonl_files = sorted(proj_dir.glob("*.jsonl"))

        if not jsonl_files:
            continue

        for jsonl_path in jsonl_files:
            key = str(jsonl_path)
            current_hash = file_hash(jsonl_path)

            if not force and key in archived and archived[key]["hash"] == current_hash:
                skipped_count += 1
                continue

            is_update = key in archived
            result = archive_transcript(jsonl_path, dry_run=dry_run)

            if result is None:
                trivial_count += 1
                continue

            output_path, metadata = result

            if not dry_run:
                archived[key] = {
                    "hash": current_hash,
                    "output": output_path,
                    "project": project_name,
                    "archived_at": datetime.now(timezone.utc).isoformat(),
                    "messages": metadata["message_count"],
                }

            if is_update:
                updated_count += 1
            else:
                new_count += 1

    if not dry_run:
        save_index(index)

    # Summary
    action = "Would archive" if dry_run else "Archived"
    print(f"\nTranscript archive {'dry run' if dry_run else 'complete'}:")
    print(f"  {action}: {new_count} new, {updated_count} updated")
    print(f"  Skipped: {skipped_count} unchanged, {trivial_count} trivial (<2 messages)")
    print(f"  Total tracked: {len(archived)}")


if __name__ == "__main__":
    main()
