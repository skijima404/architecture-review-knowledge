#!/usr/bin/env python3
"""
Compare generated edges with existing Markdown files.

This script loads the generated YAML and compares the edges
with the relationships defined in existing Markdown files.

Usage:
    python scripts/compare_edges.py
    python scripts/compare_edges.py --yaml output/node_list.yaml
"""

import argparse
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcp_server.parser import parse_node


def load_yaml(yaml_path: Path) -> dict:
    """Load the generated YAML file."""
    with open(yaml_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_existing_relations(repo_root: Path) -> dict[str, dict]:
    """Load relations from existing Markdown files.

    Returns:
        Dict mapping node_id to relations dict
    """
    relations: dict[str, dict] = {}

    for dir_name in ["root_cause", "symptom", "success_criteria"]:
        dir_path = repo_root / dir_name
        if not dir_path.exists():
            continue

        for md_file in dir_path.glob("*.md"):
            try:
                node = parse_node(md_file)
                relations[node.id] = {
                    "triggers": set(node.relations.triggers),
                    "triggered_by": set(node.relations.triggered_by),
                    "threatens": set(node.relations.threatens),
                    "threatened_by": set(node.relations.threatened_by),
                    "leads_to": set(node.relations.leads_to),
                    "leads_from": set(node.relations.leads_from),
                }
            except Exception as e:
                print(f"Warning: Could not parse {md_file}: {e}")

    return relations


def build_miro_to_node_id_map(yaml_data: dict) -> dict[str, str]:
    """Build mapping from miro_id to node_id."""
    mapping: dict[str, str] = {}

    for node_type in ["success_criteria", "symptom", "root_cause"]:
        for node in yaml_data.get(node_type, []):
            miro_id = node.get("miro_id")
            node_id = node.get("existing_match") or node.get("id")
            if miro_id and node_id:
                mapping[miro_id] = node_id

    return mapping


def extract_generated_relations(yaml_data: dict, miro_to_node: dict) -> dict[str, dict]:
    """Extract relations from generated YAML.

    Returns:
        Dict mapping node_id to relations dict
    """
    relations: dict[str, dict] = {}

    for node_type in ["success_criteria", "symptom", "root_cause"]:
        for node in yaml_data.get(node_type, []):
            node_id = node.get("existing_match") or node.get("id")
            edges = node.get("edges", {})

            if node_id not in relations:
                relations[node_id] = {
                    "triggers": set(),
                    "triggered_by": set(),
                    "threatens": set(),
                    "threatened_by": set(),
                    "leads_to": set(),
                    "leads_from": set(),
                }

            # Convert miro_ids to node_ids
            for edge_type in ["triggers", "triggered_by", "threatens", "threatened_by", "leads_to", "leads_from"]:
                for miro_id in edges.get(edge_type, []):
                    target_node_id = miro_to_node.get(miro_id)
                    if target_node_id:
                        relations[node_id][edge_type].add(target_node_id)

    return relations


def compare_relations(
    existing: dict[str, dict],
    generated: dict[str, dict],
) -> dict:
    """Compare existing and generated relations.

    Returns:
        Comparison results
    """
    results = {
        "matched": 0,
        "missing_in_generated": [],  # In existing but not in generated
        "extra_in_generated": [],    # In generated but not in existing
        "node_details": {},
    }

    all_node_ids = set(existing.keys()) | set(generated.keys())

    for node_id in sorted(all_node_ids):
        existing_rels = existing.get(node_id, {})
        generated_rels = generated.get(node_id, {})

        node_result = {
            "matched": [],
            "missing": [],
            "extra": [],
        }

        for edge_type in ["triggers", "triggered_by", "threatens", "threatened_by", "leads_to", "leads_from"]:
            existing_set = existing_rels.get(edge_type, set())
            generated_set = generated_rels.get(edge_type, set())

            # Matched
            matched = existing_set & generated_set
            for target in matched:
                node_result["matched"].append(f"{edge_type} → {target}")
                results["matched"] += 1

            # Missing in generated
            missing = existing_set - generated_set
            for target in missing:
                node_result["missing"].append(f"{edge_type} → {target}")
                results["missing_in_generated"].append(f"{node_id}.{edge_type} → {target}")

            # Extra in generated
            extra = generated_set - existing_set
            for target in extra:
                node_result["extra"].append(f"{edge_type} → {target}")
                results["extra_in_generated"].append(f"{node_id}.{edge_type} → {target}")

        if node_result["matched"] or node_result["missing"] or node_result["extra"]:
            results["node_details"][node_id] = node_result

    return results


def print_results(results: dict) -> None:
    """Print comparison results."""
    print("\n" + "=" * 70)
    print("Edge Comparison Results")
    print("=" * 70)

    print(f"\n✅ Matched edges: {results['matched']}")
    print(f"❌ Missing in generated: {len(results['missing_in_generated'])}")
    print(f"➕ Extra in generated: {len(results['extra_in_generated'])}")

    if results["missing_in_generated"]:
        print("\n" + "-" * 70)
        print("❌ Missing in Generated (exists in Markdown but not detected from Miro)")
        print("-" * 70)
        for item in sorted(results["missing_in_generated"])[:20]:
            print(f"   {item}")
        if len(results["missing_in_generated"]) > 20:
            print(f"   ... and {len(results['missing_in_generated']) - 20} more")

    if results["extra_in_generated"]:
        print("\n" + "-" * 70)
        print("➕ Extra in Generated (detected from Miro but not in Markdown)")
        print("-" * 70)
        for item in sorted(results["extra_in_generated"])[:20]:
            print(f"   {item}")
        if len(results["extra_in_generated"]) > 20:
            print(f"   ... and {len(results['extra_in_generated']) - 20} more")

    print("\n" + "=" * 70)

    # Calculate accuracy
    total_existing = results["matched"] + len(results["missing_in_generated"])
    if total_existing > 0:
        recall = results["matched"] / total_existing * 100
        print(f"\nRecall (detected / existing): {recall:.1f}%")

    total_generated = results["matched"] + len(results["extra_in_generated"])
    if total_generated > 0:
        precision = results["matched"] / total_generated * 100
        print(f"Precision (correct / generated): {precision:.1f}%")


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare generated edges with existing Markdown")
    parser.add_argument(
        "--yaml",
        default="output/node_list.yaml",
        help="Path to generated YAML file",
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Repository root path",
    )

    args = parser.parse_args()

    # Determine paths
    script_dir = Path(__file__).parent.parent
    yaml_path = script_dir / args.yaml
    repo_root = Path(args.repo_root) if args.repo_root else script_dir.parent

    print(f"📄 YAML file: {yaml_path}")
    print(f"📁 Repository root: {repo_root}")

    if not yaml_path.exists():
        print(f"❌ Error: YAML file not found: {yaml_path}")
        print("   Run 'python -m src.miro_client.cli' first to generate it.")
        return 1

    # Load data
    print("\n📖 Loading generated YAML...")
    yaml_data = load_yaml(yaml_path)

    print("📖 Loading existing Markdown files...")
    existing_relations = load_existing_relations(repo_root)
    print(f"   Found {len(existing_relations)} nodes with relations")

    # Build mappings
    print("\n🔄 Building mappings...")
    miro_to_node = build_miro_to_node_id_map(yaml_data)
    print(f"   {len(miro_to_node)} miro_id → node_id mappings")

    generated_relations = extract_generated_relations(yaml_data, miro_to_node)
    print(f"   {len(generated_relations)} nodes with generated relations")

    # Compare
    print("\n🔍 Comparing relations...")
    results = compare_relations(existing_relations, generated_relations)

    # Print results
    print_results(results)

    return 0


if __name__ == "__main__":
    sys.exit(main())

