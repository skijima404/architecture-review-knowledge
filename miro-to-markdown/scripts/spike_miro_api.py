#!/usr/bin/env python3
"""
Spike: Test Miro API connection and fetch sticky notes from a board.

Usage:
    1. Create .env file with MIRO_ACCESS_TOKEN and MIRO_BOARD_ID
    2. Run: python scripts/spike_miro_api.py
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

ACCESS_TOKEN = os.getenv("MIRO_ACCESS_TOKEN")
BOARD_ID = os.getenv("MIRO_BOARD_ID")


def test_with_miro_sdk():
    """Test using the official Miro Python SDK."""
    try:
        from miro_api import MiroApi

        # MiroApi uses access_token directly
        miro = MiroApi(ACCESS_TOKEN)

        print("=" * 60)
        print("Testing Miro API with official SDK")
        print("=" * 60)

        # Get board info
        board = miro.get_specific_board(BOARD_ID)
        print(f"\n✅ Board: {board.name}")
        print(f"   ID: {board.id}")
        print(f"   Description: {board.description or '(none)'}")

        # Get all items
        print("\n📋 Fetching items...")
        items_response = miro.get_items(BOARD_ID)
        items = items_response.data if items_response.data else []
        print(f"   Total items: {len(items)}")

        # Filter sticky notes
        sticky_notes = [item for item in items if getattr(item, "type", "") == "sticky_note"]
        print(f"   Sticky notes: {len(sticky_notes)}")

        # Display sticky notes
        if sticky_notes:
            print("\n📝 Sticky Notes:")
            for i, note in enumerate(sticky_notes[:10], 1):  # Show first 10
                data = getattr(note, "data", None)
                content = getattr(data, "content", "(no content)") if data else "(no content)"
                # Strip HTML tags for display
                import re
                clean_content = re.sub(r"<[^>]+>", "", str(content))
                print(f"   {i}. {clean_content[:60]}...")
                
                # Show style info if available
                style = getattr(note, "style", None)
                if style:
                    fill_color = getattr(style, "fill_color", None)
                    if fill_color:
                        print(f"      Color: {fill_color}")

        return True

    except ImportError:
        print("❌ miro-api package not installed. Run: pip install miro-api")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_with_requests():
    """Test using raw HTTP requests (fallback)."""
    try:
        import requests

        print("=" * 60)
        print("Testing Miro API with raw requests")
        print("=" * 60)

        headers = {
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json",
        }

        # Get board info
        response = requests.get(
            f"https://api.miro.com/v2/boards/{BOARD_ID}",
            headers=headers,
        )
        response.raise_for_status()
        board = response.json()
        print(f"\n✅ Board: {board.get('name')}")

        # Get items
        response = requests.get(
            f"https://api.miro.com/v2/boards/{BOARD_ID}/items",
            headers=headers,
            params={"limit": 50},
        )
        response.raise_for_status()
        items = response.json()
        
        print(f"\n📋 Items fetched: {len(items.get('data', []))}")
        
        # Filter and display sticky notes
        sticky_notes = [
            item for item in items.get("data", [])
            if item.get("type") == "sticky_note"
        ]
        print(f"   Sticky notes: {len(sticky_notes)}")

        if sticky_notes:
            print("\n📝 Sticky Notes (with colors):")
            print("-" * 70)
            
            # Collect unique colors
            color_map = {}
            
            for i, note in enumerate(sticky_notes[:20], 1):
                content = note.get("data", {}).get("content", "(no content)")
                style = note.get("style", {})
                fill_color = style.get("fillColor", "unknown")
                
                import re
                clean_content = re.sub(r"<[^>]+>", "", content)
                
                # Track colors
                if fill_color not in color_map:
                    color_map[fill_color] = []
                color_map[fill_color].append(clean_content[:40])
                
                print(f"   {i:2}. [{fill_color:15}] {clean_content[:50]}...")
            
            print("\n📊 Color Summary:")
            print("-" * 70)
            for color, notes in color_map.items():
                print(f"   {color}: {len(notes)} notes")
                for n in notes[:3]:
                    print(f"      - {n}...")

        # Get connectors (lines)
        print("\n🔗 Fetching connectors (lines)...")
        response = requests.get(
            f"https://api.miro.com/v2/boards/{BOARD_ID}/connectors",
            headers=headers,
            params={"limit": 50},
        )
        response.raise_for_status()
        connectors_data = response.json()
        
        connectors = connectors_data.get("data", [])
        print(f"   Found {len(connectors)} connectors")
        
        if connectors:
            print("\n📎 Connector Details (first 5):")
            print("-" * 70)
            for i, conn in enumerate(connectors[:5], 1):
                print(f"\n   Connector {i}:")
                print(f"      ID: {conn.get('id')}")
                
                # Check start point
                start = conn.get("startItem", {})
                if start:
                    print(f"      Start Item ID: {start.get('id')}")
                else:
                    start_pos = conn.get("startPosition", {})
                    print(f"      Start Position: x={start_pos.get('x')}, y={start_pos.get('y')}")
                
                # Check end point
                end = conn.get("endItem", {})
                if end:
                    print(f"      End Item ID: {end.get('id')}")
                else:
                    end_pos = conn.get("endPosition", {})
                    print(f"      End Position: x={end_pos.get('x')}, y={end_pos.get('y')}")
                
                # Style info
                style = conn.get("style", {})
                if style:
                    print(f"      Style: color={style.get('color')}, strokeStyle={style.get('strokeStyle')}")
            
            # Summary
            print("\n📊 Connector Summary:")
            print("-" * 70)
            has_start_item = sum(1 for c in connectors if c.get("startItem"))
            has_end_item = sum(1 for c in connectors if c.get("endItem"))
            print(f"   Connectors with startItem ID: {has_start_item}/{len(connectors)}")
            print(f"   Connectors with endItem ID: {has_end_item}/{len(connectors)}")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    if not ACCESS_TOKEN:
        print("❌ MIRO_ACCESS_TOKEN not set in .env")
        sys.exit(1)
    if not BOARD_ID:
        print("❌ MIRO_BOARD_ID not set in .env")
        sys.exit(1)

    print(f"🔑 Token: {ACCESS_TOKEN[:20]}...")
    print(f"📌 Board ID: {BOARD_ID}")

    # Try SDK first, fallback to requests
    if not test_with_miro_sdk():
        print("\n--- Falling back to raw requests ---\n")
        test_with_requests()


if __name__ == "__main__":
    main()

