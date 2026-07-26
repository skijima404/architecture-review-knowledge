"""YAML exporter for Miro node data.

Generates intermediate YAML files for review before Markdown generation.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import yaml

from .connectors import Edge, EdgeWarning


@dataclass
class NodeEdges:
    """Edge relationships for a node."""

    triggers: list[str] = field(default_factory=list)
    triggered_by: list[str] = field(default_factory=list)
    threatens: list[str] = field(default_factory=list)
    threatened_by: list[str] = field(default_factory=list)
    leads_to: list[str] = field(default_factory=list)
    leads_from: list[str] = field(default_factory=list)


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
    edges: NodeEdges = field(default_factory=NodeEdges)
    phase: list[str] | None = None  # TOGAF phase(s) detected from position


def create_export_data(
    nodes: list[ExportedNode],
    board_id: str,
    board_name: str,
    warnings: list[EdgeWarning] | None = None,
) -> dict:
    """Create the export data structure.

    Args:
        nodes: List of ExportedNode objects
        board_id: Miro board ID
        board_name: Miro board name
        warnings: Optional list of EdgeWarning objects

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
        # Build edges dict, only including non-empty lists
        edges_dict = {}
        if node.edges.triggers:
            edges_dict["triggers"] = node.edges.triggers
        if node.edges.triggered_by:
            edges_dict["triggered_by"] = node.edges.triggered_by
        if node.edges.threatens:
            edges_dict["threatens"] = node.edges.threatens
        if node.edges.threatened_by:
            edges_dict["threatened_by"] = node.edges.threatened_by
        if node.edges.leads_to:
            edges_dict["leads_to"] = node.edges.leads_to
        if node.edges.leads_from:
            edges_dict["leads_from"] = node.edges.leads_from

        node_data = {
            "id": node.id,
            "title": node.title,
            "miro_id": node.miro_id,
            "existing_match": node.existing_match,
        }

        # Add phase field with appropriate name based on node type
        if node.phase:
            if node.node_type == "root_cause":
                node_data["introduced_in_phase"] = node.phase
            else:  # symptom, success_criteria
                node_data["observed_in_phase"] = node.phase

        if edges_dict:
            node_data["edges"] = edges_dict

        grouped[node.node_type].append(node_data)

    # Sort each group by ID
    for node_type in grouped:
        grouped[node_type].sort(key=lambda x: x["id"])

    result = {
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

    # Add warnings if any
    if warnings:
        warnings_dict: dict[str, list[dict]] = {
            "disconnected_connectors": [],
            "unknown_edge_types": [],
        }
        for w in warnings:
            warning_data = {
                "connector_id": w.connector_id,
                **w.details,
            }
            if w.warning_type == "disconnected":
                warnings_dict["disconnected_connectors"].append(warning_data)
            elif w.warning_type == "unknown_edge_type":
                warnings_dict["unknown_edge_types"].append(warning_data)

        # Only include non-empty warning lists
        result["_warnings"] = {
            k: v for k, v in warnings_dict.items() if v
        }

    return result


def export_to_yaml(
    nodes: list[ExportedNode],
    board_id: str,
    board_name: str,
    output_path: Path,
    warnings: list[EdgeWarning] | None = None,
) -> Path:
    """Export nodes to a YAML file.

    Args:
        nodes: List of ExportedNode objects
        board_id: Miro board ID
        board_name: Miro board name
        output_path: Path for the output file
        warnings: Optional list of EdgeWarning objects

    Returns:
        Path to the generated file
    """
    data = create_export_data(nodes, board_id, board_name, warnings)

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


def print_summary(
    nodes: list[ExportedNode],
    edges: list[Edge] | None = None,
    warnings: list[EdgeWarning] | None = None,
) -> None:
    """Print a summary of exported nodes and edges.

    Args:
        nodes: List of ExportedNode objects
        edges: Optional list of Edge objects
        warnings: Optional list of EdgeWarning objects
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

    # Edge summary
    if edges:
        print("\n" + "-" * 60)
        print("Edges")
        print("-" * 60)
        edge_counts: dict[str, int] = {}
        for edge in edges:
            edge_counts[edge.edge_type] = edge_counts.get(edge.edge_type, 0) + 1
        for edge_type, count in sorted(edge_counts.items()):
            print(f"  {edge_type}: {count}")
        print(f"\n  Total: {len(edges)} edges")

    # Warnings summary
    if warnings:
        print("\n" + "-" * 60)
        print("⚠️  Warnings (require manual review)")
        print("-" * 60)
        warning_counts: dict[str, int] = {}
        for w in warnings:
            warning_counts[w.warning_type] = warning_counts.get(w.warning_type, 0) + 1
        for warning_type, count in sorted(warning_counts.items()):
            print(f"  {warning_type}: {count}")

    print("=" * 60)

