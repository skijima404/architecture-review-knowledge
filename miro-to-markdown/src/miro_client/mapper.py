"""Node type mapping from Miro sticky note attributes.

Maps Miro sticky note colors to Backcasting node types.
"""

import re
from dataclasses import dataclass

from .api import MiroStickyNote

# Color to node type mapping
COLOR_TO_NODE_TYPE: dict[str, str] = {
    "red": "success_criteria",
    "light_yellow": "symptom",
    "light_blue": "root_cause",
}

# Colors to ignore (memos, notes, etc.)
IGNORED_COLORS: set[str] = {"gray"}

# Titles to ignore (header labels, legends, etc.)
EXCLUDED_TITLES: set[str] = {
    "success criteria",
    "symptom",
    "root cause",
}

# ID prefix for each node type
NODE_TYPE_TO_PREFIX: dict[str, str] = {
    "success_criteria": "sc",
    "symptom": "rf",
    "root_cause": "rc",
}


@dataclass
class MappedNode:
    """A Miro sticky note mapped to a Backcasting node."""

    miro_id: str
    title: str
    node_type: str
    id_prefix: str
    position_x: float
    position_y: float
    raw_content: str


def strip_html_tags(html: str) -> str:
    """Remove HTML tags from a string.

    Args:
        html: String potentially containing HTML tags

    Returns:
        Clean text without HTML tags
    """
    # Remove HTML tags
    clean = re.sub(r"<[^>]+>", "", html)
    # Normalize whitespace
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean


def get_node_type(fill_color: str) -> str | None:
    """Get node type from fill color.

    Args:
        fill_color: Miro sticky note fill color

    Returns:
        Node type string, or None if color should be ignored
    """
    if fill_color in IGNORED_COLORS:
        return None
    return COLOR_TO_NODE_TYPE.get(fill_color)


def is_excluded_title(title: str) -> bool:
    """Check if a title should be excluded (header label, legend, etc.).

    Args:
        title: Cleaned title text

    Returns:
        True if title should be excluded
    """
    return title.lower().strip() in EXCLUDED_TITLES


def map_sticky_note(sticky_note: MiroStickyNote) -> MappedNode | None:
    """Map a Miro sticky note to a Backcasting node.

    Args:
        sticky_note: MiroStickyNote from API

    Returns:
        MappedNode if mappable, None if should be ignored
    """
    node_type = get_node_type(sticky_note.fill_color)
    if node_type is None:
        return None

    title = strip_html_tags(sticky_note.content)
    if not title:
        return None

    # Skip header labels / legends
    if is_excluded_title(title):
        return None

    id_prefix = NODE_TYPE_TO_PREFIX[node_type]

    return MappedNode(
        miro_id=sticky_note.miro_id,
        title=title,
        node_type=node_type,
        id_prefix=id_prefix,
        position_x=sticky_note.position_x,
        position_y=sticky_note.position_y,
        raw_content=sticky_note.content,
    )


def map_all_sticky_notes(sticky_notes: list[MiroStickyNote]) -> list[MappedNode]:
    """Map all sticky notes, filtering out ignored colors.

    Args:
        sticky_notes: List of MiroStickyNote objects

    Returns:
        List of MappedNode objects (only valid nodes)
    """
    mapped = []
    for note in sticky_notes:
        node = map_sticky_note(note)
        if node is not None:
            mapped.append(node)
    return mapped

