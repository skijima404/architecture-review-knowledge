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
from .exporter import ExportedNode, export_to_yaml, print_summary
from .mapper import map_all_sticky_notes
from .matcher import NodeMatcher


def get_repo_root() -> Path:
    """Get the repository root path.

    Returns:
        Path to the repository root (parent of miro-to-markdown)
    """
    # This file is at: miro-to-markdown/src/miro_client/cli.py
    # Repo root is: miro-to-markdown/../
    return Path(__file__).parent.parent.parent.parent


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

    args = parser.parse_args()

    if not args.board_id:
        print("❌ Error: Board ID required. Set MIRO_BOARD_ID in .env or use --board-id")
        return 1

    # Determine paths
    repo_root = Path(args.repo_root) if args.repo_root else get_repo_root()
    output_path = Path(__file__).parent.parent.parent / args.output

    print(f"🔑 Using board ID: {args.board_id}")
    print(f"📁 Repository root: {repo_root}")
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
        matcher = NodeMatcher(repo_root)
        print(f"   Found {len(matcher.existing_nodes)} existing nodes in repository")

        # Create export nodes
        exported_nodes: list[ExportedNode] = []
        for node in mapped_nodes:
            assigned_id, existing_match = matcher.match_or_generate_id(
                node.title,
                node.node_type,
                node.id_prefix,
            )
            exported_nodes.append(
                ExportedNode(
                    id=assigned_id,
                    title=node.title,
                    node_type=node.node_type,
                    miro_id=node.miro_id,
                    existing_match=existing_match,
                    position_x=node.position_x,
                    position_y=node.position_y,
                )
            )

        # Export to YAML
        print(f"\n💾 Exporting to {output_path}...")
        export_to_yaml(exported_nodes, args.board_id, board_name, output_path)

        # Print summary
        print_summary(exported_nodes)

        print(f"\n✅ Done! Review the file at: {output_path}")
        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

