"""Command-line interface for Markdown generation.

Usage:
    python -m src.miro_client.generate_cli --input output/node_list.yaml
    python -m src.miro_client.generate_cli --input output/node_list.yaml --dry-run
"""

import argparse
import sys
from pathlib import Path

from .generator import GenerationResult, GeneratorConfig, generate_all


def get_repo_root() -> Path:
    """Get the repository root path.

    Returns:
        Path to the repository root (parent of miro-to-markdown)
    """
    return Path(__file__).parent.parent.parent.parent


def get_miro_to_markdown_root() -> Path:
    """Get the miro-to-markdown folder path.

    Returns:
        Path to miro-to-markdown folder
    """
    return Path(__file__).parent.parent.parent


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success)
    """
    parser = argparse.ArgumentParser(
        description="Generate Markdown files from YAML export"
    )
    parser.add_argument(
        "--input",
        "-i",
        default="output/node_list.yaml",
        help="Input YAML file (default: output/node_list.yaml)",
    )
    parser.add_argument(
        "--config",
        "-c",
        default="config.yaml",
        help="Config file path (default: config.yaml)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be created without writing files",
    )

    args = parser.parse_args()

    # Resolve paths
    miro_root = get_miro_to_markdown_root()
    repo_root = get_repo_root()

    yaml_path = miro_root / args.input
    config_path = miro_root / args.config

    # Check if config exists, try local version first
    local_config = miro_root / "config.local.yaml"
    if local_config.exists():
        config_path = local_config
        print(f"📄 Using local config: {config_path}")
    elif not config_path.exists():
        print(f"❌ Config file not found: {config_path}")
        return 1

    if not yaml_path.exists():
        print(f"❌ Input YAML not found: {yaml_path}")
        print("   Run the export CLI first: python -m src.miro_client.cli")
        return 1

    print(f"📄 Input YAML: {yaml_path}")
    print(f"⚙️  Config: {config_path}")
    print(f"📁 Repository root: {repo_root}")

    if args.dry_run:
        print("\n🔍 DRY RUN - No files will be written\n")

    try:
        # Load config
        config = GeneratorConfig.from_yaml(config_path)
        print(f"\n📂 Output base path: {config.base_path}")
        print(f"   Folders:")
        for node_type, folder in config.folders.items():
            full_path = config.get_output_folder(node_type, repo_root, miro_root)
            print(f"     {node_type}: {full_path}")

        # Generate Markdown files
        print("\n🔄 Generating Markdown files...")
        result = generate_all(
            yaml_path=yaml_path,
            config=config,
            repo_root=repo_root,
            miro_root=miro_root,
            dry_run=args.dry_run,
        )

        # Print results
        print("\n" + "=" * 60)
        print("Generation Summary")
        print("=" * 60)

        if result.created:
            action = "Would create" if args.dry_run else "Created"
            print(f"\n✅ {action} {len(result.created)} new files:")
            for path in result.created:
                print(f"   📝 {path}")

        if result.skipped:
            print(f"\n⏭️  Skipped {len(result.skipped)} existing nodes:")
            for node_id in result.skipped[:10]:
                print(f"   {node_id}")
            if len(result.skipped) > 10:
                print(f"   ... and {len(result.skipped) - 10} more")

        print("\n" + "=" * 60)

        if args.dry_run:
            print("\n💡 Run without --dry-run to create files")
        else:
            print(f"\n✅ Done! {len(result.created)} files created")

        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

