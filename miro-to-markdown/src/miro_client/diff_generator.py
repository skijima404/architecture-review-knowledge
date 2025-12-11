"""Diff generator for existing nodes.

Compares Miro export with existing Markdown files and generates
a diff report for edges and phases.
"""

from dataclasses import dataclass, field
from pathlib import Path
import re

import frontmatter
import yaml


@dataclass
class EdgeDiff:
    """Difference in edges for a node."""

    node_id: str
    edge_type: str
    added: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)


@dataclass
class PhaseDiff:
    """Difference in phase for a node."""

    node_id: str
    field_name: str  # introduced_in_phase or observed_in_phase
    current: list[str]
    new: list[str]


@dataclass
class NodeDiff:
    """All differences for a single node."""

    node_id: str
    node_type: str
    file_path: Path
    edge_diffs: list[EdgeDiff] = field(default_factory=list)
    phase_diff: PhaseDiff | None = None

    @property
    def has_changes(self) -> bool:
        """Check if there are any changes."""
        return bool(self.edge_diffs) or self.phase_diff is not None


def parse_wikilinks(value: list | None) -> set[str]:
    """Extract node IDs from wikilink list.

    Args:
        value: List like ["[[rc-001]]", "[[rc-002]]"]

    Returns:
        Set of node IDs like {"rc-001", "rc-002"}
    """
    if not value:
        return set()

    ids = set()
    for item in value:
        if isinstance(item, str):
            match = re.search(r"\[\[([^\]]+)\]\]", item)
            if match:
                ids.add(match.group(1))
    return ids


def load_existing_node(file_path: Path) -> dict | None:
    """Load frontmatter from existing Markdown file.

    Args:
        file_path: Path to Markdown file

    Returns:
        Frontmatter dict or None if file doesn't exist
    """
    if not file_path.exists():
        return None

    try:
        post = frontmatter.load(file_path)
        return dict(post.metadata)
    except Exception:
        return None


def get_edge_fields(node_type: str) -> list[str]:
    """Get edge field names for a node type.

    Args:
        node_type: Node type

    Returns:
        List of edge field names
    """
    if node_type == "success_criteria":
        return ["threatened_by"]
    elif node_type == "symptom":
        return ["triggered_by", "triggers", "threatens"]
    elif node_type == "root_cause":
        return ["leads_from", "triggers", "leads_to"]
    return []


def get_phase_field(node_type: str) -> str:
    """Get phase field name for a node type.

    Args:
        node_type: Node type

    Returns:
        Phase field name
    """
    if node_type == "root_cause":
        return "introduced_in_phase"
    return "observed_in_phase"


def compare_node(
    miro_node: dict,
    existing_fm: dict,
    node_type: str,
    file_path: Path,
    miro_to_node: dict[str, str],
) -> NodeDiff | None:
    """Compare Miro node with existing Markdown.

    Args:
        miro_node: Node data from Miro export
        existing_fm: Frontmatter from existing file
        node_type: Node type
        file_path: Path to existing file
        miro_to_node: Mapping from miro_id to node_id

    Returns:
        NodeDiff if there are changes, None otherwise
    """
    node_id = miro_node.get("existing_match") or miro_node.get("id")
    diff = NodeDiff(
        node_id=node_id,
        node_type=node_type,
        file_path=file_path,
    )

    # Compare edges
    miro_edges = miro_node.get("edges", {})
    edge_fields = get_edge_fields(node_type)

    for edge_field in edge_fields:
        # Get Miro edges (convert miro_ids to node_ids)
        miro_targets = set()
        for miro_id in miro_edges.get(edge_field, []):
            node_id_target = miro_to_node.get(miro_id)
            if node_id_target:
                miro_targets.add(node_id_target)

        # Get existing edges
        existing_targets = parse_wikilinks(existing_fm.get(edge_field))

        # Calculate diff
        added = miro_targets - existing_targets
        removed = existing_targets - miro_targets

        if added or removed:
            diff.edge_diffs.append(EdgeDiff(
                node_id=node_id,
                edge_type=edge_field,
                added=sorted(added),
                removed=sorted(removed),
            ))

    # Compare phase
    phase_field = get_phase_field(node_type)
    miro_phase = miro_node.get(phase_field, [])
    existing_phase = existing_fm.get(phase_field, [])

    # Normalize to lists
    if isinstance(existing_phase, str):
        existing_phase = [existing_phase]

    if set(miro_phase) != set(existing_phase):
        diff.phase_diff = PhaseDiff(
            node_id=node_id,
            field_name=phase_field,
            current=existing_phase,
            new=miro_phase,
        )

    return diff if diff.has_changes else None


def resolve_miro_ids_to_node_ids(
    nodes_by_type: dict[str, list[dict]],
) -> dict[str, str]:
    """Build mapping from miro_id to node_id."""
    mapping = {}
    for nodes in nodes_by_type.values():
        for node in nodes:
            miro_id = node.get("miro_id")
            node_id = node.get("existing_match") or node.get("id")
            if miro_id and node_id:
                mapping[miro_id] = node_id
    return mapping


def generate_diff_report(
    yaml_path: Path,
    repo_root: Path,
    node_folders: dict[str, str],
) -> list[NodeDiff]:
    """Generate diff report for all existing nodes.

    Args:
        yaml_path: Path to Miro export YAML
        repo_root: Repository root path
        node_folders: Mapping of node_type to folder name

    Returns:
        List of NodeDiff objects with changes
    """
    with open(yaml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    nodes_by_type = {
        "success_criteria": data.get("success_criteria", []),
        "symptom": data.get("symptom", []),
        "root_cause": data.get("root_cause", []),
    }

    miro_to_node = resolve_miro_ids_to_node_ids(nodes_by_type)
    diffs: list[NodeDiff] = []

    for node_type, nodes in nodes_by_type.items():
        folder_name = node_folders.get(node_type, node_type)
        folder_path = repo_root / folder_name

        for miro_node in nodes:
            existing_match = miro_node.get("existing_match")
            if not existing_match:
                continue  # New node, not a diff

            file_path = folder_path / f"{existing_match}.md"
            existing_fm = load_existing_node(file_path)

            if not existing_fm:
                continue  # File doesn't exist

            node_diff = compare_node(
                miro_node=miro_node,
                existing_fm=existing_fm,
                node_type=node_type,
                file_path=file_path,
                miro_to_node=miro_to_node,
            )

            if node_diff:
                diffs.append(node_diff)

    return diffs


def export_diff_yaml(diffs: list[NodeDiff], output_path: Path) -> None:
    """Export diff report to YAML file.

    Args:
        diffs: List of NodeDiff objects
        output_path: Output file path
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "summary": {
            "total_nodes_with_changes": len(diffs),
            "edge_changes": sum(len(d.edge_diffs) for d in diffs),
            "phase_changes": sum(1 for d in diffs if d.phase_diff),
        },
        "changes": [],
    }

    for diff in diffs:
        node_data = {
            "node_id": diff.node_id,
            "node_type": diff.node_type,
            "file": str(diff.file_path),
        }

        if diff.edge_diffs:
            node_data["edge_changes"] = []
            for ed in diff.edge_diffs:
                edge_change = {"field": ed.edge_type}
                if ed.added:
                    edge_change["add"] = ed.added
                if ed.removed:
                    edge_change["remove"] = ed.removed
                node_data["edge_changes"].append(edge_change)

        if diff.phase_diff:
            node_data["phase_change"] = {
                "field": diff.phase_diff.field_name,
                "current": diff.phase_diff.current,
                "new": diff.phase_diff.new,
            }

        data["changes"].append(node_data)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Diff Report: Miro vs Existing Markdown\n")
        f.write("# Review changes below and apply with: python -m src.miro_client.apply_diff\n\n")
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

