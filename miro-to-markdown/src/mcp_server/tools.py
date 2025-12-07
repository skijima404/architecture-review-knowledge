"""Backcasting MCP Tools implementation."""

import json
from dataclasses import asdict
from pathlib import Path

import frontmatter

from .models import (
    BackcastingChain,
    BackcastingNode,
    BackcastingTemplate,
    ChainNode,
    NodeType,
)
from .parser import parse_node, parse_template, validate_frontmatter


class BackcastingTools:
    """Implementation of Backcasting MCP tools."""

    def __init__(self, repo_root: Path):
        """Initialize with repository root path.

        Args:
            repo_root: Path to the architecture-review-knowledge repository root
        """
        self.repo_root = repo_root
        self.templates_dir = repo_root / "templates"
        self.node_type_to_dir: dict[str, str] = {
            "root_cause": "root_cause",
            "symptom": "symptom",
            "success_criteria": "success_criteria",
        }

    def get_template(self, node_type: NodeType) -> dict:
        """Get a template for creating a new node of the given type.

        Args:
            node_type: One of 'root_cause', 'symptom', 'success_criteria'

        Returns:
            BackcastingTemplate as a dictionary

        Raises:
            FileNotFoundError: If template file doesn't exist
            ValueError: If node_type is invalid
        """
        if node_type not in self.node_type_to_dir:
            raise ValueError(
                f"Invalid node_type: {node_type}. "
                f"Must be one of: {list(self.node_type_to_dir.keys())}"
            )

        template_path = self.templates_dir / f"{node_type}.md"
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")

        template = parse_template(template_path)
        return asdict(template)

    def get_node(self, node_id: str) -> dict:
        """Fetch a single Backcasting node by ID.

        Args:
            node_id: Node ID (e.g., 'rc-001', 'rf-002', 'sc-003')

        Returns:
            BackcastingNode as a dictionary

        Raises:
            FileNotFoundError: If node file doesn't exist
            ValueError: If node_id format is invalid
        """
        node_path = self._resolve_node_path(node_id)
        if not node_path.exists():
            raise FileNotFoundError(f"Node not found: {node_path}")

        node = parse_node(node_path)
        # Update path to be relative to repo root
        node.path = str(node_path.relative_to(self.repo_root))
        return asdict(node)

    def write_node(self, node_id: str, markdown: str, path: str | None = None) -> dict:
        """Create or update a Backcasting node on disk.

        Args:
            node_id: Node ID (must match id in frontmatter)
            markdown: Full file contents (frontmatter + body)
            path: Optional relative path; if not provided, inferred from node_id

        Returns:
            BackcastingNode as a dictionary (re-parsed after write)

        Raises:
            ValueError: If frontmatter is invalid or id doesn't match
        """
        # Parse and validate the markdown
        post = frontmatter.loads(markdown)
        errors = validate_frontmatter(post)
        if errors:
            raise ValueError(f"Invalid frontmatter: {'; '.join(errors)}")

        # Verify ID matches
        frontmatter_id = post.get("id", "")
        if frontmatter_id != node_id:
            raise ValueError(
                f"ID mismatch: provided node_id='{node_id}' "
                f"but frontmatter id='{frontmatter_id}'"
            )

        # Determine output path
        if path:
            output_path = self.repo_root / path
        else:
            output_path = self._resolve_node_path(node_id)

        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write the file
        output_path.write_text(markdown, encoding="utf-8")

        # Re-parse and return the node
        node = parse_node(output_path)
        node.path = str(output_path.relative_to(self.repo_root))
        return asdict(node)

    def _resolve_node_path(self, node_id: str) -> Path:
        """Resolve a node ID to its file path.

        Convention:
            - rc-XXX -> root_cause/rc-XXX.md
            - rf-XXX -> symptom/rf-XXX.md
            - sc-XXX -> success_criteria/sc-XXX.md

        Args:
            node_id: Node ID

        Returns:
            Path to the node file

        Raises:
            ValueError: If node_id prefix is unrecognized
        """
        prefix_to_dir = {
            "rc-": "root_cause",
            "rf-": "symptom",
            "sc-": "success_criteria",
        }

        for prefix, directory in prefix_to_dir.items():
            if node_id.startswith(prefix):
                return self.repo_root / directory / f"{node_id}.md"

        raise ValueError(
            f"Unrecognized node_id prefix: {node_id}. "
            f"Expected one of: {list(prefix_to_dir.keys())}"
        )

    def get_chain_from_root(
        self,
        root_id: str,
        max_depth: int = 10,
        include_markdown: bool = False,
    ) -> dict:
        """Return a causal chain from a Root Cause to Success Criteria.

        Traverses the graph following:
          - root_cause: triggers → symptoms
          - symptom: triggers → symptoms, threatens → success_criteria

        Args:
            root_id: ID of the starting root_cause node
            max_depth: Maximum traversal depth (default 10)
            include_markdown: If True, include markdown in node data (not implemented in v1)

        Returns:
            BackcastingChain as a dictionary

        Raises:
            FileNotFoundError: If root node doesn't exist
            ValueError: If root_id is not a root_cause
        """
        if not root_id.startswith("rc-"):
            raise ValueError(f"root_id must be a root_cause (rc-*), got: {root_id}")

        # Track visited nodes to avoid cycles
        visited: set[str] = set()
        # Collect all nodes in the chain
        chain_nodes: list[ChainNode] = []
        # Collect paths (for now, single representative path)
        paths: list[list[str]] = []

        def traverse(node_id: str, current_path: list[str], depth: int) -> None:
            """Recursively traverse the chain."""
            if depth > max_depth:
                return
            if node_id in visited:
                return

            try:
                node_path = self._resolve_node_path(node_id)
                if not node_path.exists():
                    return
            except ValueError:
                return

            visited.add(node_id)
            node = parse_node(node_path)

            chain_node = ChainNode(
                id=node.id,
                node_type=node.node_type,
                title=node.title,
            )
            chain_nodes.append(chain_node)

            new_path = current_path + [node_id]

            # If this is a success_criteria, we've reached an end point
            if node.node_type == "success_criteria":
                paths.append(new_path)
                return

            # Follow 'triggers' relationships (RC → SYM, SYM → SYM)
            for triggered_id in node.relations.triggers:
                traverse(triggered_id, new_path, depth + 1)

            # Follow 'threatens' relationships (SYM → SC)
            for threatened_id in node.relations.threatens:
                traverse(threatened_id, new_path, depth + 1)

        # Start traversal from root
        traverse(root_id, [], 0)

        chain = BackcastingChain(
            type="backcasting_chain",
            direction="root_to_success_criteria",
            root_id=root_id,
            nodes=chain_nodes,
            paths=paths,
        )

        return asdict(chain)


def to_json(data: dict) -> str:
    """Convert a dictionary to JSON string with nice formatting."""
    return json.dumps(data, indent=2, ensure_ascii=False)

