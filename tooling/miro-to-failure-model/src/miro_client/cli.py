"""Command-line interface for Miro to Markdown export.

Usage:
    python -m src.miro_client.cli --board-id <BOARD_ID>
    python -m src.miro_client.cli  # Uses MIRO_BOARD_ID from .env
"""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from .api import get_miro_client
from .connectors import Edge, fetch_connectors, process_connectors
from .exporter import ExportedNode, NodeEdges, export_to_yaml, print_summary
from .generator import GeneratorConfig
from .mapper import map_all_sticky_notes
from .matcher import NodeMatcher
from .phase_detector import PhaseDetector


def get_tool_root() -> Path:
    """Get the Miro-to-Failure-Model tool path."""
    return Path(__file__).parent.parent.parent


def get_repo_root() -> Path:
    """Get the repository root path."""
    return get_tool_root().parent.parent


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success)
    """
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Export Miro board sticky notes to YAML for Backcasting"
    )
    parser.add_argument(
        "--board-id",
        default=os.getenv("MIRO_BOARD_ID"),
        help="Miro board ID (default: MIRO_BOARD_ID from .env)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="output/node_list.yaml",
        help="Output file path (default: output/node_list.yaml)",
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Repository root path (default: auto-detected)",
    )
    parser.add_argument(
        "--config",
        "-c",
        default="config.yaml",
        help="Config file path (default: config.yaml)",
    )

    args = parser.parse_args()

    if not args.board_id:
        print("❌ Error: Board ID required. Set MIRO_BOARD_ID in .env or use --board-id")
        return 1

    # Determine paths
    miro_root = get_tool_root()
    repo_root = Path(args.repo_root) if args.repo_root else get_repo_root()
    output_path = miro_root / args.output

    # Load config
    config_path = miro_root / args.config
    local_config = miro_root / "config.local.yaml"
    if local_config.exists():
        config_path = local_config
        print(f"📄 Using local config: {config_path}")

    config = GeneratorConfig.from_yaml(config_path)

    # Determine base path for existing node check
    if config.base_path_str.startswith("./"):
        check_base_path = (miro_root / config.base_path).resolve()
    else:
        check_base_path = (repo_root / config.base_path).resolve()

    print(f"🔑 Using board ID: {args.board_id}")
    print(f"📁 Repository root: {repo_root}")
    print(f"📁 Check existing in: {check_base_path}")
    print(f"📄 Output file: {output_path}")

    try:
        # Get Miro client
        client = get_miro_client()

        # Get board name
        print("\n📋 Fetching board info...")
        board_name = client.get_board_name(args.board_id)
        print(f"   Board: {board_name}")

        # Fetch sticky notes
        print("\n📝 Fetching sticky notes...")
        sticky_notes = list(client.get_sticky_notes(args.board_id))
        print(f"   Found {len(sticky_notes)} sticky notes")

        # Map to nodes
        print("\n🔄 Mapping nodes...")
        mapped_nodes = map_all_sticky_notes(sticky_notes)
        print(f"   Mapped {len(mapped_nodes)} valid nodes")

        # Match with existing nodes
        print("\n🔍 Matching with existing nodes...")
        matcher = NodeMatcher(check_base_path, config.folders)
        print(f"   Found {len(matcher.existing_nodes)} existing nodes in {check_base_path}")

        # Initialize phase detector
        print("\n📍 Detecting TOGAF phases...")
        access_token = os.getenv("MIRO_ACCESS_TOKEN")
        phase_detector = PhaseDetector(args.board_id, access_token)
        print(f"   Found {len(phase_detector.phase_ranges)} phase columns: ", end="")
        print(", ".join(pr.phase for pr in phase_detector.phase_ranges))

        # Create export nodes and build miro_id mapping
        exported_nodes: list[ExportedNode] = []
        miro_id_to_node: dict[str, dict] = {}

        for node in mapped_nodes:
            assigned_id, existing_match = matcher.match_or_generate_id(
                node.title,
                node.node_type,
                node.id_prefix,
            )

            # Detect phase based on X position
            detected_phase = phase_detector.detect(node.position_x)

            exported_node = ExportedNode(
                id=assigned_id,
                title=node.title,
                node_type=node.node_type,
                miro_id=node.miro_id,
                existing_match=existing_match,
                position_x=node.position_x,
                position_y=node.position_y,
                phase=detected_phase,
            )
            exported_nodes.append(exported_node)

            # Build mapping for edge processing
            miro_id_to_node[node.miro_id] = {
                "node_type": node.node_type,
                "position_x": node.position_x,
                "exported_node": exported_node,
            }

        # Fetch and process connectors
        print("\n🔗 Fetching connectors...")
        connectors = fetch_connectors(args.board_id)
        print(f"   Found {len(connectors)} connectors")

        print("\n🔄 Processing edges...")
        edges, warnings = process_connectors(connectors, miro_id_to_node)
        print(f"   Extracted {len(edges)} edges")
        if warnings:
            print(f"   ⚠️  {len(warnings)} warnings")

        # Add edges to exported nodes
        # Edge types:
        #   Forward: triggers, threatens, leads_to (source → target)
        #   Backward: triggered_by, threatened_by, leads_from (source ← target)
        for edge in edges:
            source_node_data = miro_id_to_node.get(edge.from_miro_id)
            target_node_data = miro_id_to_node.get(edge.to_miro_id)

            if not source_node_data or not target_node_data:
                continue

            source_node = source_node_data["exported_node"]
            target_node = target_node_data["exported_node"]

            # Forward edge types: add to source, add reverse to target
            if edge.edge_type == "triggers":
                source_node.edges.triggers.append(edge.to_miro_id)
                target_node.edges.triggered_by.append(edge.from_miro_id)
            elif edge.edge_type == "threatens":
                source_node.edges.threatens.append(edge.to_miro_id)
                target_node.edges.threatened_by.append(edge.from_miro_id)
            elif edge.edge_type == "leads_to":
                source_node.edges.leads_to.append(edge.to_miro_id)
                target_node.edges.leads_from.append(edge.from_miro_id)
            # Backward edge types: add to source, add reverse to target
            elif edge.edge_type == "leads_from":
                source_node.edges.leads_from.append(edge.to_miro_id)
                target_node.edges.leads_to.append(edge.from_miro_id)
            elif edge.edge_type == "triggered_by":
                source_node.edges.triggered_by.append(edge.to_miro_id)
                target_node.edges.triggers.append(edge.from_miro_id)

        # Export to YAML
        print(f"\n💾 Exporting to {output_path}...")
        export_to_yaml(exported_nodes, args.board_id, board_name, output_path, warnings)

        # Print summary
        print_summary(exported_nodes, edges, warnings)

        print(f"\n✅ Done! Review the file at: {output_path}")
        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
