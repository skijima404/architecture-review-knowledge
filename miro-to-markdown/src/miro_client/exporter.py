"""YAML exporter for Miro node data.

Generates intermediate YAML files for review before Markdown generation.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import yaml

from .mapper import MappedNode


@dataclass
class ExportedNode:
    """A node ready for export to YAML."""

    id: str
    title: str
    node_type: str
    miro_id: str
    existing_match: str | None
    position_x: float
    position_y: float


def create_export_data(
    nodes: list[ExportedNode],
    board_id: str,
    board_name: str,
) -> dict:
    """Create the export data structure.

    Args:
        nodes: List of ExportedNode objects
        board_id: Miro board ID
        board_name: Miro board name

    Returns:
        Dictionary ready for YAML export
    """
    # Group by node type
    grouped: dict[str, list[dict]] = {
        "success_criteria": [],
        "symptom": [],
        "root_cause": [],
    }

    for node in nodes:
        node_data = {
            "id": node.id,
            "title": node.title,
            "miro_id": node.miro_id,
            "existing_match": node.existing_match,
        }
        grouped[node.node_type].append(node_data)

    # Sort each group by ID
    for node_type in grouped:
        grouped[node_type].sort(key=lambda x: x["id"])

    return {
        "metadata": {
            "board_id": board_id,
            "board_name": board_name,
            "generated_at": datetime.now().isoformat(),
            "total_nodes": len(nodes),
        },
        "success_criteria": grouped["success_criteria"],
        "symptom": grouped["symptom"],
        "root_cause": grouped["root_cause"],
    }


def export_to_yaml(
    nodes: list[ExportedNode],
    board_id: str,
    board_name: str,
    output_path: Path,
) -> Path:
    """Export nodes to a YAML file.

    Args:
        nodes: List of ExportedNode objects
        board_id: Miro board ID
        board_name: Miro board name
        output_path: Path for the output file

    Returns:
        Path to the generated file
    """
    data = create_export_data(nodes, board_id, board_name)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write YAML with nice formatting
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Backcasting Node List\n")
        f.write(f"# Generated from Miro board: {board_name}\n")
        f.write(f"# Board ID: {board_id}\n")
        f.write(f"# Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("#\n")
        f.write("# Review this file and adjust IDs if needed.\n")
        f.write("# Then run the Markdown generator.\n")
        f.write("\n")

        yaml.dump(
            data,
            f,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
            width=120,
        )

    return output_path


def print_summary(nodes: list[ExportedNode]) -> None:
    """Print a summary of exported nodes.

    Args:
        nodes: List of ExportedNode objects
    """
    # Count by type
    counts: dict[str, int] = {}
    matched: dict[str, int] = {}

    for node in nodes:
        counts[node.node_type] = counts.get(node.node_type, 0) + 1
        if node.existing_match:
            matched[node.node_type] = matched.get(node.node_type, 0) + 1

    print("\n" + "=" * 60)
    print("Export Summary")
    print("=" * 60)

    for node_type in ["success_criteria", "symptom", "root_cause"]:
        count = counts.get(node_type, 0)
        match_count = matched.get(node_type, 0)
        new_count = count - match_count
        print(f"  {node_type}: {count} total ({match_count} matched, {new_count} new)")

    print(f"\n  Total: {len(nodes)} nodes")
    print("=" * 60)

