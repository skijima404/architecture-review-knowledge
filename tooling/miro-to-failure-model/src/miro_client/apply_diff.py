"""Apply diff to existing Markdown files.

Reads a diff YAML file and applies edge/phase changes to existing files.
"""

import re
from pathlib import Path

import frontmatter
import yaml


def parse_wikilinks(value: list | None) -> list[str]:
    """Extract node IDs from wikilink list, preserving order."""
    if not value:
        return []

    ids = []
    for item in value:
        if isinstance(item, str):
            match = re.search(r"\[\[([^\]]+)\]\]", item)
            if match:
                ids.append(match.group(1))
    return ids


def format_wikilinks(ids: list[str]) -> list[str]:
    """Format node IDs as wikilinks."""
    return [f'"[[{id}]]"' for id in sorted(ids)]


def apply_edge_changes(
    post: frontmatter.Post,
    edge_changes: list[dict],
) -> bool:
    """Apply edge changes to a post.

    Args:
        post: Frontmatter post object
        edge_changes: List of edge change dicts

    Returns:
        True if any changes were made
    """
    changed = False

    for change in edge_changes:
        field = change.get("field")
        add = change.get("add", [])
        remove = change.get("remove", [])

        # Get current values
        current = parse_wikilinks(post.metadata.get(field, []))
        current_set = set(current)

        # Apply changes
        new_set = current_set.copy()
        for item in add:
            new_set.add(item)
        for item in remove:
            new_set.discard(item)

        if new_set != current_set:
            # Update metadata
            post.metadata[field] = [f"[[{id}]]" for id in sorted(new_set)]
            changed = True

    return changed


def apply_phase_change(
    post: frontmatter.Post,
    phase_change: dict,
) -> bool:
    """Apply phase change to a post.

    Args:
        post: Frontmatter post object
        phase_change: Phase change dict

    Returns:
        True if change was made
    """
    field = phase_change.get("field")
    new_value = phase_change.get("new", [])

    current = post.metadata.get(field, [])
    if isinstance(current, str):
        current = [current]

    if set(new_value) != set(current):
        post.metadata[field] = new_value
        return True

    return False


def apply_diff_file(
    diff_path: Path,
    dry_run: bool = False,
) -> tuple[int, int]:
    """Apply diff file to existing Markdown files.

    Args:
        diff_path: Path to diff YAML file
        dry_run: If True, don't actually modify files

    Returns:
        Tuple of (files_updated, changes_applied)
    """
    with open(diff_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    changes = data.get("changes", [])
    files_updated = 0
    changes_applied = 0

    for change in changes:
        file_path = Path(change.get("file"))
        node_id = change.get("node_id")

        if not file_path.exists():
            print(f"⚠️  File not found: {file_path}")
            continue

        # Load file
        post = frontmatter.load(file_path)
        file_changed = False

        # Apply edge changes
        edge_changes = change.get("edge_changes", [])
        if edge_changes:
            if apply_edge_changes(post, edge_changes):
                file_changed = True
                changes_applied += len(edge_changes)
                for ec in edge_changes:
                    field = ec.get("field")
                    add = ec.get("add", [])
                    remove = ec.get("remove", [])
                    if add:
                        print(f"  📝 {node_id}.{field}: +{add}")
                    if remove:
                        print(f"  📝 {node_id}.{field}: -{remove}")

        # Apply phase change
        phase_change = change.get("phase_change")
        if phase_change:
            if apply_phase_change(post, phase_change):
                file_changed = True
                changes_applied += 1
                field = phase_change.get("field")
                new_val = phase_change.get("new")
                print(f"  📝 {node_id}.{field}: → {new_val}")

        # Save file
        if file_changed and not dry_run:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(frontmatter.dumps(post))
            files_updated += 1

    return files_updated, changes_applied


def main() -> int:
    """Main entry point."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Apply diff to existing Markdown files"
    )
    parser.add_argument(
        "--input",
        "-i",
        default="output/diff_report.yaml",
        help="Diff YAML file (default: output/diff_report.yaml)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show changes without applying",
    )

    args = parser.parse_args()

    # Resolve path
    miro_root = Path(__file__).parent.parent.parent
    diff_path = miro_root / args.input

    if not diff_path.exists():
        print(f"❌ Diff file not found: {diff_path}")
        print("   Run diff generation first: python -m src.miro_client.diff_cli")
        return 1

    print(f"📄 Diff file: {diff_path}")

    if args.dry_run:
        print("\n🔍 DRY RUN - No files will be modified\n")

    print("\n🔄 Applying changes...")
    files_updated, changes_applied = apply_diff_file(diff_path, args.dry_run)

    print("\n" + "=" * 60)
    if args.dry_run:
        print(f"Would update {files_updated} files with {changes_applied} changes")
        print("\n💡 Run without --dry-run to apply changes")
    else:
        print(f"✅ Updated {files_updated} files with {changes_applied} changes")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

