"""Path helpers for reusable PR200 reverse/debug artifacts."""

from __future__ import annotations

import os
from pathlib import Path


def resolve_pr200_reverse_file(anchor_file: str | Path, filename: str) -> Path:
    """Resolve a PR200 reverse artifact without assuming a single checkout layout."""

    anchor = Path(anchor_file).resolve()
    tool_dir = anchor.parent
    candidates: list[Path] = []

    if env_dir := os.environ.get("OWEN_PR200_REVERSE_DIR"):
        candidates.append(Path(env_dir) / filename)

    candidates.append(tool_dir / "pr200_reverse" / filename)

    for parent in (tool_dir, *tool_dir.parents):
        candidates.append(parent / "examples" / "avr-3in1-pr200" / "artifacts" / "pr200_reverse" / filename)

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return candidates[0]
