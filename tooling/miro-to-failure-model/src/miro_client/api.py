"""Miro REST API Client.

This module provides an abstraction layer for Miro API access.
"""

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterator

import requests
from dotenv import load_dotenv


@dataclass
class MiroStickyNote:
    """Represents a sticky note from Miro board."""

    miro_id: str
    content: str
    fill_color: str
    position_x: float = 0.0
    position_y: float = 0.0


class MiroClientBase(ABC):
    """Abstract base class for Miro clients."""

    @abstractmethod
    def get_board_name(self, board_id: str) -> str:
        """Get the name of a board."""
        pass

    @abstractmethod
    def get_sticky_notes(self, board_id: str) -> Iterator[MiroStickyNote]:
        """Get all sticky notes from a board."""
        pass


class MiroRestClient(MiroClientBase):
    """Miro REST API client implementation."""

    BASE_URL = "https://api.miro.com/v2"

    def __init__(self, access_token: str | None = None):
        """Initialize with access token.

        Args:
            access_token: Miro API access token. If not provided,
                          reads from MIRO_ACCESS_TOKEN environment variable.
        """
        load_dotenv()
        self.access_token = access_token or os.getenv("MIRO_ACCESS_TOKEN")
        if not self.access_token:
            raise ValueError(
                "Miro access token required. Set MIRO_ACCESS_TOKEN environment variable."
            )

        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    def get_board_name(self, board_id: str) -> str:
        """Get the name of a board.

        Args:
            board_id: Miro board ID

        Returns:
            Board name
        """
        response = requests.get(
            f"{self.BASE_URL}/boards/{board_id}",
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json().get("name", "")

    def get_sticky_notes(self, board_id: str) -> Iterator[MiroStickyNote]:
        """Get all sticky notes from a board.

        Args:
            board_id: Miro board ID

        Yields:
            MiroStickyNote objects
        """
        cursor = None

        while True:
            params = {"limit": 50, "type": "sticky_note"}
            if cursor:
                params["cursor"] = cursor

            response = requests.get(
                f"{self.BASE_URL}/boards/{board_id}/items",
                headers=self.headers,
                params=params,
            )
            response.raise_for_status()
            data = response.json()

            for item in data.get("data", []):
                if item.get("type") == "sticky_note":
                    yield MiroStickyNote(
                        miro_id=str(item.get("id", "")),
                        content=item.get("data", {}).get("content", ""),
                        fill_color=item.get("style", {}).get("fillColor", "unknown"),
                        position_x=item.get("position", {}).get("x", 0.0),
                        position_y=item.get("position", {}).get("y", 0.0),
                    )

            # Check for next page
            cursor = data.get("cursor")
            if not cursor:
                break


def get_miro_client(access_token: str | None = None) -> MiroClientBase:
    """Factory function to get the Miro REST client.

    Args:
        access_token: Optional access token

    Returns:
        MiroClientBase implementation
    """
    return MiroRestClient(access_token)
