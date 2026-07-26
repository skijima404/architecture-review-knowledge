#!/usr/bin/env python3
"""
Debug script to check node positions and RC→RC connectors.
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


def fetch_items_with_positions():
    """Fetch all items with their positions."""
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    
    items = []
    cursor = None
    
    while True:
        params = {"limit": 50}
        if cursor:
            params["cursor"] = cursor
            
        response = requests.get(
            f"https://api.miro.com/v2/boards/{BOARD_ID}/items",
            headers=headers,
            params=params,
        )
        response.raise_for_status()
        data = response.json()
        
        for item in data.get("data", []):
            if item.get("type") == "sticky_note":
                position = item.get("position", {})
                items.append({
                    "miro_id": str(item.get("id")),
                    "x": position.get("x", 0),
                    "y": position.get("y", 0),
                    "content": item.get("data", {}).get("content", ""),
                    "color": item.get("style", {}).get("fillColor", ""),
                })
        
        cursor = data.get("cursor")
        if not cursor:
            break
    
    return items


def fetch_connectors():
    """Fetch all connectors."""
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
    # Load YAML to get node mappings
    script_dir = Path(__file__).parent.parent
    yaml_path = script_dir / "output" / "node_list.yaml"
    yaml_data = load_yaml(yaml_path)
    
    # Build miro_id -> node_id mapping
    miro_to_node = {}
    for node_type in ["success_criteria", "symptom", "root_cause"]:
        for node in yaml_data.get(node_type, []):
            miro_id = node.get("miro_id")
            node_id = node.get("existing_match") or node.get("id")
            if miro_id:
                miro_to_node[miro_id] = node_id
    
    # Fetch items with positions
    print("Fetching items with positions...")
    items = fetch_items_with_positions()
    miro_id_to_item = {item["miro_id"]: item for item in items}
    print(f"  Found {len(items)} sticky notes")
    
    # Fetch connectors
    print("Fetching connectors...")
    connectors = fetch_connectors()
    print(f"  Found {len(connectors)} connectors")
    
    # Focus on specific nodes
    focus_nodes = ["rc-020", "rc-005", "rc-008", "rc-009", "rc-010", "rc-006", "rc-013"]
    
    print("\n" + "=" * 70)
    print("Focus Node Positions")
    print("=" * 70)
    
    focus_miro_ids = set()
    for node_id in focus_nodes:
        for miro_id, nid in miro_to_node.items():
            if nid == node_id:
                item = miro_id_to_item.get(miro_id, {})
                print(f"  {node_id}: miro_id={miro_id}, x={item.get('x')}, y={item.get('y')}")
                focus_miro_ids.add(miro_id)
    
    # Find RC→RC connectors involving focus nodes
    print("\n" + "=" * 70)
    print("RC→RC Connectors involving focus nodes")
    print("=" * 70)
    
    for conn in connectors:
        start_id = str(conn.get("startItem", {}).get("id")) if conn.get("startItem", {}).get("id") else None
        end_id = str(conn.get("endItem", {}).get("id")) if conn.get("endItem", {}).get("id") else None
        
        if not start_id or not end_id:
            continue
            
        # Check if both are in focus nodes
        start_node_id = miro_to_node.get(start_id)
        end_node_id = miro_to_node.get(end_id)
        
        if not start_node_id or not end_node_id:
            continue
            
        # Only RC→RC
        if not (start_node_id.startswith("rc-") and end_node_id.startswith("rc-")):
            continue
            
        if start_id in focus_miro_ids or end_id in focus_miro_ids:
            start_item = miro_id_to_item.get(start_id, {})
            end_item = miro_id_to_item.get(end_id, {})
            
            start_x = start_item.get("x", 0)
            end_x = end_item.get("x", 0)
            
            direction = "forward (leads_to)" if end_x > start_x else "backward (leads_from)"
            
            print(f"\n  Connector {conn.get('id')}")
            print(f"    Start miro_id: {start_id} → {start_node_id} (x={start_x})")
            print(f"    End miro_id:   {end_id} → {end_node_id} (x={end_x})")
            print(f"    Direction: {direction}")
            if end_x > start_x:
                print(f"    → {start_node_id}.leads_to should contain {end_node_id}")
            else:
                print(f"    → {start_node_id}.leads_from should contain {end_node_id}")


if __name__ == "__main__":
    main()

