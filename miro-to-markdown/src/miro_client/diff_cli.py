"""CLI for generating diff report.

Usage:
    python -m src.miro_client.diff_cli
"""

import argparse
import sys
from pathlib import Path

import yaml

from .diff_generator import generate_diff_report, export_diff_yaml
from .generator import GeneratorConfig


def get_repo_root() -> Path:
    """Get the repository root path."""
    return Path(__file__).parent.parent.parent.parent


def get_miro_root() -> Path:
    """Get the miro-to-markdown folder path."""
    return Path(__file__).parent.parent.parent


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate diff report between Miro export and existing Markdown"
    )
    parser.add_argument(
        "--input",
        "-i",
        default="output/node_list.yaml",
        help="Input YAML file (default: output/node_list.yaml)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="output/diff_report.yaml",
        help="Output diff file (default: output/diff_report.yaml)",
    )
    parser.add_argument(
        "--config",
        "-c",
        default="config.yaml",
        help="Config file path (default: config.yaml)",
    )

    args = parser.parse_args()

    miro_root = get_miro_root()
    repo_root = get_repo_root()

    yaml_path = miro_root / args.input
    output_path = miro_root / args.output

    # Load config for folder names
    config_path = miro_root / args.config
    local_config = miro_root / "config.local.yaml"
    if local_config.exists():
        config_path = local_config

    if not yaml_path.exists():
        print(f"❌ Input YAML not found: {yaml_path}")
        return 1

    print(f"📄 Input YAML: {yaml_path}")
    print(f"📄 Output: {output_path}")

    try:
        # Load config
        config = GeneratorConfig.from_yaml(config_path)

        # Determine base path for existing files check
        if config.base_path_str.startswith("./"):
            check_base_path = (miro_root / config.base_path).resolve()
        else:
            check_base_path = (repo_root / config.base_path).resolve()

        print(f"📁 Check existing in: {check_base_path}")

        print("\n🔍 Generating diff report...")
        diffs = generate_diff_report(
            yaml_path=yaml_path,
            repo_root=check_base_path,
            node_folders=config.folders,
        )

        if not diffs:
            print("\n✅ No differences found! Miro and Markdown are in sync.")
            return 0

        # Export to YAML
        export_diff_yaml(diffs, output_path)

        # Print summary
        print("\n" + "=" * 60)
        print("Diff Summary")
        print("=" * 60)

        edge_changes = sum(len(d.edge_diffs) for d in diffs)
        phase_changes = sum(1 for d in diffs if d.phase_diff)

        print(f"\n📊 {len(diffs)} nodes with changes:")
        print(f"   Edge changes: {edge_changes}")
        print(f"   Phase changes: {phase_changes}")

        print("\n📝 Changes by node:")
        for diff in diffs[:10]:
            print(f"\n   {diff.node_id} ({diff.node_type}):")
            for ed in diff.edge_diffs:
                if ed.added:
                    print(f"      {ed.edge_type}: +{ed.added}")
                if ed.removed:
                    print(f"      {ed.edge_type}: -{ed.removed}")
            if diff.phase_diff:
                print(f"      {diff.phase_diff.field_name}: {diff.phase_diff.current} → {diff.phase_diff.new}")

        if len(diffs) > 10:
            print(f"\n   ... and {len(diffs) - 10} more nodes")

        print("\n" + "=" * 60)
        print(f"\n💾 Diff saved to: {output_path}")
        print("💡 Apply with: python -m src.miro_client.apply_diff")

        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

