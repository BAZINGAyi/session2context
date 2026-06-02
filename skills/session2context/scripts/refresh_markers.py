#!/usr/bin/env python3
"""session2context marker refresher.

Deterministic helper for the session2context skill. The LLM generates the
semantic description lines; this script handles ONLY the deterministic parts so
that file edits are reliable and never mangle content outside the markers:

  - enumerating non-empty preference files (avoids hallucinated paths)
  - locating the single canonical injection target (priority order, mutually
    exclusive: exactly one file is ever modified)
  - safely replacing the content between the s2c markers

Subcommands (all resolve paths relative to --root, default: current directory):

  list-prefs    Print non-empty preference files (relative paths), one per line.
  find-target   Print the single target file that would be injected into.
                Prints nothing and exits 0 when no valid target exists.
  inject        Replace content between the markers in the target file with the
                text read from stdin. Exits 2 when no valid target exists.

Markers (must already exist in the target file; this script never creates files):

  <!-- s2c:start -->
  ...managed block...
  <!-- s2c:end -->
"""

import argparse
import os
import re
import sys
import tempfile
from pathlib import Path

START_MARKER = "<!-- s2c:start -->"
END_MARKER = "<!-- s2c:end -->"

# Priority order. The three locations are mutually exclusive: only the first
# file that exists AND contains a valid marker block is used.
TARGET_CANDIDATES = (
    Path(".cursor/rules/session2context.mdc"),
    Path("CLAUDE.md"),
    Path("AGENTS.md"),
)

PREFS_DIR = Path("s2c-data/preferences")

# Matches a single managed block, capturing the markers so they are preserved.
_BLOCK_RE = re.compile(
    re.escape(START_MARKER) + r"(?P<body>.*?)" + re.escape(END_MARKER),
    re.DOTALL,
)
_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)


def _has_valid_block(text):
    """Return True if text contains exactly one well-formed marker block."""
    if text.count(START_MARKER) != 1 or text.count(END_MARKER) != 1:
        return False
    return text.index(START_MARKER) < text.index(END_MARKER)


def _atomic_write(path, content):
    """Write content to path atomically (write temp in same dir, then replace)."""
    directory = path.parent
    fd, tmp_path = tempfile.mkstemp(dir=str(directory), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
        os.replace(tmp_path, str(path))
    except BaseException:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def find_target(root):
    """Return the single Path to inject into, or None when none qualifies."""
    for rel in TARGET_CANDIDATES:
        candidate = root / rel
        if not candidate.is_file():
            continue
        try:
            text = candidate.read_text(encoding="utf-8")
        except OSError:
            continue
        if _has_valid_block(text):
            return candidate
    return None


def list_prefs(root):
    """Return sorted relative paths of non-empty preference markdown files."""
    prefs_dir = root / PREFS_DIR
    if not prefs_dir.is_dir():
        return []
    results = []
    for md in sorted(prefs_dir.glob("*.md")):
        try:
            text = md.read_text(encoding="utf-8")
        except OSError:
            continue
        stripped = _COMMENT_RE.sub("", text).strip()
        if stripped:
            results.append(md.relative_to(root).as_posix())
    return results


def inject(root, block):
    """Replace the managed block in the priority target with block text.

    Returns the relative target path on success. Raises RuntimeError when no
    valid target exists or the target block is malformed.
    """
    target = find_target(root)
    if target is None:
        raise RuntimeError(
            "no injection target found: none of "
            ".cursor/rules/session2context.mdc, CLAUDE.md, AGENTS.md "
            "contains a valid <!-- s2c:start -->/<!-- s2c:end --> block"
        )

    text = target.read_text(encoding="utf-8")
    if not _has_valid_block(text):
        raise RuntimeError("target block is malformed: %s" % target)

    body = "\n" + block.strip("\n") + "\n"
    new_text = _BLOCK_RE.sub(
        lambda m: START_MARKER + body + END_MARKER,
        text,
        count=1,
    )
    if new_text != text:
        _atomic_write(target, new_text)
    return target.relative_to(root).as_posix()


def _resolve_root(value):
    root = Path(value).resolve()
    if not root.is_dir():
        sys.exit("error: --root is not a directory: %s" % root)
    return root


def main(argv=None):
    parser = argparse.ArgumentParser(description="session2context marker refresher")
    parser.add_argument(
        "--root",
        default=".",
        help="project root that contains s2c-data/ (default: current dir)",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list-prefs", help="list non-empty preference files")
    sub.add_parser("find-target", help="print the single injection target, if any")
    sub.add_parser("inject", help="replace marker block with text from stdin")

    args = parser.parse_args(argv)
    root = _resolve_root(args.root)

    if args.command == "list-prefs":
        for rel in list_prefs(root):
            print(rel)
        return 0

    if args.command == "find-target":
        target = find_target(root)
        if target is not None:
            print(target.relative_to(root).as_posix())
        return 0

    if args.command == "inject":
        block = sys.stdin.read()
        try:
            updated = inject(root, block)
        except RuntimeError as exc:
            print("error: %s" % exc, file=sys.stderr)
            return 2
        print(updated)
        return 0

    parser.error("unknown command")


if __name__ == "__main__":
    sys.exit(main())
