#!/usr/bin/env python3
"""
Debug script to find specific connectors in Miro API response.

Usage:
    python scripts/debug_connectors.py
"""

import os
import sys
from pathlib import Path

import requests
import yaml
from dotenv import load_dotenv

load_dotenv()

ACCESS_TOKEN = os.getenv("MIRO_ACCESS_TOKEN")
BOARD_ID = os.getenv("MIRO_BOARD_ID")


def load_yaml(yaml_path: Path) -> dict:
    with open(yaml_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_miro_ids_for_node(yaml_data: dict, node_id: str) -> list[str]:
    """Get all miro_ids for a given node_id."""
    miro_ids = []
    for node_type in ["success_criteria", "symptom", "root_cause"]:
        for node in yaml_data.get(node_type, []):
            if node.get("existing_match") == node_id or node.get("id") == node_id:
                miro_ids.append(node.get("miro_id"))
    return miro_ids


def fetch_all_connectors():
    """Fetch all connectors from Miro."""
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    
    connectors = []
    cursor = None
    
    while True:
        params = {"limit": 50}
        if cursor:
            params["cursor"] = cursor
            
        response = requests.get(
            f"https://api.miro.com/v2/boards/{BOARD_ID}/connectors",
            headers=headers,
            params=params,
        )
        response.raise_for_status()
        data = response.json()
        
        connectors.extend(data.get("data", []))
        
        cursor = data.get("cursor")
        if not cursor:
            break
    
    return connectors


def main():
    # Nodes to search for
    search_nodes = ["rc-003", "rf-001", "rf-004", "rf-007"]
    
    # Load YAML to get miro_ids
    script_dir = Path(__file__).parent.parent
    yaml_path = script_dir / "output" / "node_list.yaml"
    yaml_data = load_yaml(yaml_path)
    
    # Build miro_id -> node_id mapping
    node_miro_ids: dict[str, list[str]] = {}
    miro_to_node: dict[str, str] = {}
    
    for node_id in search_nodes:
        miro_ids = get_miro_ids_for_node(yaml_data, node_id)
        node_miro_ids[node_id] = miro_ids
        for mid in miro_ids:
            miro_to_node[mid] = node_id
    
    print("=" * 70)
    print("Node → Miro ID Mapping")
    print("=" * 70)
    for node_id, miro_ids in node_miro_ids.items():
        print(f"  {node_id}: {miro_ids}")
    
    # Collect all relevant miro_ids
    all_miro_ids = set()
    for miro_ids in node_miro_ids.values():
        all_miro_ids.update(miro_ids)
    
    print(f"\n  Total miro_ids to search: {len(all_miro_ids)}")
    
    # Fetch connectors
    print("\n" + "=" * 70)
    print("Fetching Connectors from Miro API...")
    print("=" * 70)
    
    connectors = fetch_all_connectors()
    print(f"  Total connectors: {len(connectors)}")
    
    # Find connectors involving our nodes
    print("\n" + "=" * 70)
    print("Connectors involving searched nodes")
    print("=" * 70)
    
    found_connectors = []
    for conn in connectors:
        start_id = conn.get("startItem", {}).get("id")
        end_id = conn.get("endItem", {}).get("id")
        
        start_id_str = str(start_id) if start_id else None
        end_id_str = str(end_id) if end_id else None
        
        start_match = start_id_str in all_miro_ids if start_id_str else False
        end_match = end_id_str in all_miro_ids if end_id_str else False
        
        if start_match or end_match:
            found_connectors.append({
                "connector_id": conn.get("id"),
                "start_item_id": start_id_str,
                "end_item_id": end_id_str,
                "start_node": miro_to_node.get(start_id_str, "???") if start_id_str else None,
                "end_node": miro_to_node.get(end_id_str, "???") if end_id_str else None,
                "raw": conn,
            })
    
    print(f"\n  Found {len(found_connectors)} connectors")
    
    for i, fc in enumerate(found_connectors, 1):
        print(f"\n  [{i}] Connector {fc['connector_id']}")
        print(f"      Start: {fc['start_item_id']} → {fc['start_node']}")
        print(f"      End:   {fc['end_item_id']} → {fc['end_node']}")
        
        # Show raw data for debugging
        raw = fc["raw"]
        print(f"      Raw startItem: {raw.get('startItem')}")
        print(f"      Raw endItem: {raw.get('endItem')}")
    
    # Specifically look for rc-003 → rf-001
    print("\n" + "=" * 70)
    print("Looking for rc-003 → rf-001 specifically")
    print("=" * 70)
    
    rc003_miro_ids = set(node_miro_ids.get("rc-003", []))
    rf001_miro_ids = set(node_miro_ids.get("rf-001", []))
    
    print(f"  rc-003 miro_ids: {rc003_miro_ids}")
    print(f"  rf-001 miro_ids: {rf001_miro_ids}")
    
    for conn in connectors:
        start_id = str(conn.get("startItem", {}).get("id")) if conn.get("startItem", {}).get("id") else None
        end_id = str(conn.get("endItem", {}).get("id")) if conn.get("endItem", {}).get("id") else None
        
        # Check both directions
        if (start_id in rc003_miro_ids and end_id in rf001_miro_ids) or \
           (start_id in rf001_miro_ids and end_id in rc003_miro_ids):
            print(f"\n  ✅ FOUND! Connector {conn.get('id')}")
            print(f"      Start: {start_id}")
            print(f"      End:   {end_id}")
            print(f"      Raw: {conn}")


if __name__ == "__main__":
    main()

