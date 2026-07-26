#!/usr/bin/env python3
"""Validate Architecture Review Knowledge structure without external packages."""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

FAILURE_MODEL_ZONES = {
    "knowledge/curated/failure-model/root-causes": ("root_cause", "rc-"),
    "knowledge/curated/failure-model/symptoms": ("symptom", "rf-"),
    "knowledge/curated/failure-model/success-criteria": (
        "success_criteria",
        "sc-",
    ),
}

RAW_REQUIRED = {
    "id",
    "type",
    "maturity",
    "review_usage",
    "created_at",
    "note_kind",
    "confidentiality",
    "topics",
}

WIKILINK = re.compile(r"\[\[([^\]]+)\]\]")


def frontmatter_text(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return ""
    _, frontmatter, _ = text.split("---", 2)
    return frontmatter


def scalar(frontmatter: str, key: str) -> str | None:
    match = re.search(rf"(?m)^{re.escape(key)}:\s*(.*?)\s*$", frontmatter)
    if not match:
        return None
    value = match.group(1).strip().strip("\"'")
    return value or None


def has_key(frontmatter: str, key: str) -> bool:
    return re.search(rf"(?m)^{re.escape(key)}:", frontmatter) is not None


def validate() -> list[str]:
    errors: list[str] = []
    ids: dict[str, Path] = {}
    node_paths: dict[str, Path] = {}
    node_frontmatter: dict[str, str] = {}

    for relative_dir, (expected_type, prefix) in FAILURE_MODEL_ZONES.items():
        directory = REPO_ROOT / relative_dir
        if not directory.is_dir():
            errors.append(f"missing Failure Model directory: {relative_dir}")
            continue

        for path in sorted(directory.glob("*.md")):
            frontmatter = frontmatter_text(path)
            if not frontmatter:
                errors.append(f"missing frontmatter: {path.relative_to(REPO_ROOT)}")
                continue

            node_id = scalar(frontmatter, "id")
            node_type = scalar(frontmatter, "type")
            relative_path = path.relative_to(REPO_ROOT)

            if not node_id:
                errors.append(f"missing id: {relative_path}")
                continue
            if node_id in ids:
                errors.append(
                    f"duplicate id {node_id}: {ids[node_id].relative_to(REPO_ROOT)} "
                    f"and {relative_path}"
                )
            ids[node_id] = path
            node_paths[node_id] = path
            node_frontmatter[node_id] = frontmatter

            if path.stem != node_id:
                errors.append(f"filename/id mismatch: {relative_path} -> {node_id}")
            if not node_id.startswith(prefix):
                errors.append(f"id prefix mismatch: {relative_path} -> {node_id}")
            if node_type != expected_type:
                errors.append(
                    f"type mismatch: {relative_path} -> {node_type!r}, "
                    f"expected {expected_type!r}"
                )

    known_ids = set(node_paths)
    for node_id, frontmatter in node_frontmatter.items():
        for target in WIKILINK.findall(frontmatter):
            if target not in known_ids:
                source = node_paths[node_id].relative_to(REPO_ROOT)
                errors.append(f"broken relation: {source} -> {target}")

    raw_root = REPO_ROOT / "knowledge/raw-notes"
    for path in sorted(raw_root.rglob("*.md")):
        if path.name == "README.md":
            continue
        frontmatter = frontmatter_text(path)
        relative_path = path.relative_to(REPO_ROOT)
        if not frontmatter:
            errors.append(f"missing Raw Note frontmatter: {relative_path}")
            continue

        missing = sorted(key for key in RAW_REQUIRED if not has_key(frontmatter, key))
        if missing:
            errors.append(f"missing Raw Note fields {missing}: {relative_path}")
        if scalar(frontmatter, "type") != "raw_note":
            errors.append(f"Raw Note type must be raw_note: {relative_path}")
        if scalar(frontmatter, "maturity") != "raw":
            errors.append(f"Raw Note maturity must be raw: {relative_path}")
        if scalar(frontmatter, "review_usage") != "prohibited":
            errors.append(f"Raw Note review_usage must be prohibited: {relative_path}")
        if scalar(frontmatter, "confidentiality") != "public_safe":
            errors.append(f"Raw Note confidentiality must be public_safe: {relative_path}")

        raw_id = scalar(frontmatter, "id")
        if raw_id:
            if raw_id in ids:
                errors.append(
                    f"duplicate id {raw_id}: {ids[raw_id].relative_to(REPO_ROOT)} "
                    f"and {relative_path}"
                )
            ids[raw_id] = path

    for zone in ("knowledge/raw-notes", "knowledge/candidates"):
        for path in (REPO_ROOT / zone).rglob("*.md"):
            if path.name == "README.md":
                continue
            frontmatter = frontmatter_text(path)
            if scalar(frontmatter, "review_usage") == "allowed":
                errors.append(
                    f"non-curated asset permits Production use: "
                    f"{path.relative_to(REPO_ROOT)}"
                )

    forbidden_active_paths = (
        REPO_ROOT / "tooling/miro-to-failure-model/src/mcp_server",
        REPO_ROOT / "tooling/miro-to-failure-model/docs/backcasting-mcp-spec.md",
    )
    for path in forbidden_active_paths:
        if path.exists():
            errors.append(f"retired MCP asset remains active: {path.relative_to(REPO_ROOT)}")

    required_traceability = (
        "docs/traceability/enabler-proposals/"
        "ep-001-knowledge-lifecycle-and-trust-zones.md",
        "docs/traceability/value-streams/vs-001-raw-to-curated-knowledge.md",
        "docs/traceability/implementation-specs/is-001-raw-notes-foundation.md",
        "policies/retrieval-policy.md",
        "schemas/raw-note-template.md",
        "schemas/failure-model/node-spec.md",
    )
    for relative_path in required_traceability:
        if not (REPO_ROOT / relative_path).is_file():
            errors.append(f"missing required repository contract: {relative_path}")

    print(
        f"Validated {len(node_paths)} Failure Model nodes and "
        f"{sum(1 for path in raw_root.rglob('*.md') if path.name != 'README.md')} "
        "Raw Notes."
    )
    return errors


def main() -> int:
    errors = validate()
    if errors:
        print(f"\n{len(errors)} validation error(s):")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Repository validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
