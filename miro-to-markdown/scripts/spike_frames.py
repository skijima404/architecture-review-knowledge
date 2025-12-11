#!/usr/bin/env python3
"""Spike: Check Miro frames for Phase detection."""

import os

import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("MIRO_ACCESS_TOKEN")
BOARD_ID = os.getenv("MIRO_BOARD_ID")

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}


def fetch_all_items():
    """Fetch all items from the board."""
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
        items.extend(data.get("data", []))
        
        cursor = data.get("cursor")
        if not cursor:
            break
    
    return items


def main():
    print("=" * 70)
    print("Miro Board Items by Type")
    print("=" * 70)
    
    items = fetch_all_items()
    
    # Group by type
    by_type = {}
    for item in items:
        item_type = item.get("type", "unknown")
        if item_type not in by_type:
            by_type[item_type] = []
        by_type[item_type].append(item)
    
    print(f"\nFound {len(items)} total items\n")
    
    for item_type, type_items in sorted(by_type.items()):
        print(f"\n{'=' * 70}")
        print(f"{item_type.upper()} ({len(type_items)} items)")
        print("=" * 70)
        
        for item in type_items[:10]:  # Show first 10
            item_id = item.get("id")
            position = item.get("position", {})
            x = position.get("x", "N/A")
            y = position.get("y", "N/A")
            geometry = item.get("geometry", {})
            width = geometry.get("width", "N/A")
            height = geometry.get("height", "N/A")
            
            # Get title/content based on type
            if item_type == "frame":
                title = item.get("data", {}).get("title", "Untitled")
            elif item_type == "shape":
                content = item.get("data", {}).get("content", "")
                title = content[:50] if content else "No content"
            elif item_type == "sticky_note":
                content = item.get("data", {}).get("content", "")
                title = content[:50] if content else "No content"
            elif item_type == "text":
                content = item.get("data", {}).get("content", "")
                title = content[:50] if content else "No content"
            else:
                title = str(item.get("data", {}))[:50]
            
            print(f"\n  ID: {item_id}")
            print(f"  Title/Content: {title}")
            print(f"  Position: x={x}, y={y}")
            print(f"  Size: {width} x {height}")
        
        if len(type_items) > 10:
            print(f"\n  ... and {len(type_items) - 10} more")


if __name__ == "__main__":
    main()

