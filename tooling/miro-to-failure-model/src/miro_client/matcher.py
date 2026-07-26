"""Existing node matching.

Matches Miro sticky notes to existing Markdown files by title.
"""

import re
from dataclasses import dataclass
from pathlib import Path

import frontmatter


@dataclass
class ExistingNode:
    """An existing Backcasting node from the repository."""

    id: str
    title: str
    node_type: str
    path: Path


def normalize_title(title: str) -> str:
    """Normalize a title for comparison.

    Args:
        title: Original title

    Returns:
        Normalized title (lowercase, no extra whitespace)
    """
    # Lowercase
    normalized = title.lower()
    # Remove extra whitespace
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def load_existing_nodes(
    base_path: Path,
    folders: dict[str, str] | None = None,
) -> list[ExistingNode]:
    """Load all existing Backcasting nodes from the specified path.

    Args:
        base_path: Base path to search for nodes
        folders: Mapping of node_type to folder name (optional)

    Returns:
        List of ExistingNode objects
    """
    nodes = []

    # Canonical Failure Model directories
    if folders is None:
        folders = {
            "root_cause": "knowledge/curated/failure-model/root-causes",
            "symptom": "knowledge/curated/failure-model/symptoms",
            "success_criteria": "knowledge/curated/failure-model/success-criteria",
        }

    for node_type, dir_name in folders.items():
        dir_path = base_path / dir_name
        if not dir_path.exists():
            continue

        for md_file in dir_path.glob("*.md"):
            try:
                post = frontmatter.load(md_file)
                node_id = post.get("id", "")
                title = post.get("title", "")
                file_type = post.get("type", node_type)

                if node_id and title:
                    nodes.append(
                        ExistingNode(
                            id=node_id,
                            title=title,
                            node_type=file_type,
                            path=md_file,
                        )
                    )
            except Exception:
                # Skip files that can't be parsed
                continue

    return nodes


def find_matching_node(
    title: str,
    node_type: str,
    existing_nodes: list[ExistingNode],
) -> ExistingNode | None:
    """Find an existing node that matches the given title.

    Args:
        title: Title to match
        node_type: Expected node type
        existing_nodes: List of existing nodes to search

    Returns:
        Matching ExistingNode, or None if not found
    """
    normalized_title = normalize_title(title)

    for node in existing_nodes:
        # Must match node type
        if node.node_type != node_type:
            continue

        # Compare normalized titles
        if normalize_title(node.title) == normalized_title:
            return node

    return None


def get_next_id(id_prefix: str, existing_nodes: list[ExistingNode]) -> str:
    """Generate the next available ID for a node type.

    Args:
        id_prefix: ID prefix (e.g., "rc", "rf", "sc")
        existing_nodes: List of existing nodes

    Returns:
        Next available ID (e.g., "rc-042")
    """
    # Find all existing IDs with this prefix
    pattern = re.compile(rf"^{id_prefix}-(\d+)$")
    max_num = 0

    for node in existing_nodes:
        match = pattern.match(node.id)
        if match:
            num = int(match.group(1))
            max_num = max(max_num, num)

    # Return next ID
    return f"{id_prefix}-{max_num + 1:03d}"


class NodeMatcher:
    """Matches Miro nodes to existing repository nodes."""

    def __init__(
        self,
        base_path: Path,
        folders: dict[str, str] | None = None,
    ):
        """Initialize with base path and folder configuration.

        Args:
            base_path: Base path to search for existing nodes
            folders: Mapping of node_type to folder name (optional)
        """
        self.base_path = base_path
        self.folders = folders
        self.existing_nodes = load_existing_nodes(base_path, folders)
        self._id_counters: dict[str, int] = {}

    def match_or_generate_id(
        self,
        title: str,
        node_type: str,
        id_prefix: str,
    ) -> tuple[str, str | None]:
        """Match to existing node or generate new ID.

        Args:
            title: Node title
            node_type: Node type
            id_prefix: ID prefix for this type

        Returns:
            Tuple of (assigned_id, existing_match_id or None)
        """
        # Try to find existing match
        existing = find_matching_node(title, node_type, self.existing_nodes)

        if existing:
            return existing.id, existing.id

        # Generate new ID
        if id_prefix not in self._id_counters:
            # Initialize counter based on existing nodes
            base_id = get_next_id(id_prefix, self.existing_nodes)
            self._id_counters[id_prefix] = int(base_id.split("-")[1])

        new_id = f"{id_prefix}-{self._id_counters[id_prefix]:03d}"
        self._id_counters[id_prefix] += 1

        return new_id, None
