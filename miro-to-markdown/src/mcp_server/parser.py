"""Frontmatter parser for Backcasting Markdown files."""

import re
from pathlib import Path

import frontmatter

from .models import (
    BackcastingNode,
    BackcastingTemplate,
    FrontmatterSchema,
    NodeType,
    PhaseInfo,
    Relations,
)

# Pattern to extract node ID from wikilink syntax: [[rc-001]] -> rc-001
WIKILINK_PATTERN = re.compile(r"\[\[([^\]]+)\]\]")


def extract_ids_from_wikilinks(values: list[str] | None) -> list[str]:
    """Extract node IDs from wikilink syntax.

    Args:
        values: List of strings potentially containing [[id]] syntax

    Returns:
        List of extracted IDs
    """
    if not values:
        return []

    ids = []
    for value in values:
        if isinstance(value, str):
            match = WIKILINK_PATTERN.search(value)
            if match:
                ids.append(match.group(1))
            else:
                # If no wikilink syntax, use the value as-is
                ids.append(value)
    return ids


def parse_template(template_path: Path) -> BackcastingTemplate:
    """Parse a template Markdown file into a BackcastingTemplate.

    Args:
        template_path: Path to the template file

    Returns:
        BackcastingTemplate with parsed content
    """
    content = template_path.read_text(encoding="utf-8")
    post = frontmatter.loads(content)

    node_type: NodeType = post.get("type", "root_cause")

    return BackcastingTemplate(
        type="backcasting_template",
        node_type=node_type,
        frontmatter_schema=FrontmatterSchema(),
        markdown=content,
    )


def parse_node(node_path: Path) -> BackcastingNode:
    """Parse a Backcasting Markdown file into a BackcastingNode.

    Args:
        node_path: Path to the Markdown file

    Returns:
        BackcastingNode with parsed frontmatter and content
    """
    content = node_path.read_text(encoding="utf-8")
    post = frontmatter.loads(content)

    # Required fields
    node_id: str = post.get("id", "")
    title: str = post.get("title", "")
    node_type: NodeType = post.get("type", "root_cause")

    # Phase info
    phase = PhaseInfo(
        observed_in_phase=post.get("observed_in_phase", []) or [],
        introduced_in_phase=post.get("introduced_in_phase", []) or [],
        reviewable_in_phase=post.get("reviewable_in_phase", []) or [],
    )

    # Relations (extract IDs from wikilinks)
    relations = Relations(
        leads_from=extract_ids_from_wikilinks(post.get("leads_from")),
        triggered_by=extract_ids_from_wikilinks(post.get("triggered_by")),
        triggers=extract_ids_from_wikilinks(post.get("triggers")),
        leads_to=extract_ids_from_wikilinks(post.get("leads_to")),
        threatens=extract_ids_from_wikilinks(post.get("threatens")),
        threatened_by=extract_ids_from_wikilinks(post.get("threatened_by")),
        related_success_criteria=extract_ids_from_wikilinks(
            post.get("related_success_criteria")
        ),
        tags=post.get("tags", []) or [],
    )

    return BackcastingNode(
        type="backcasting_node",
        id=node_id,
        title=title,
        node_type=node_type,
        phase=phase,
        relations=relations,
        markdown=content,
        path=str(node_path),
    )


def validate_frontmatter(post: frontmatter.Post) -> list[str]:
    """Validate that required frontmatter fields are present.

    Args:
        post: Parsed frontmatter post

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    required = ["id", "title", "type"]

    for field in required:
        if field not in post.metadata:
            errors.append(f"Missing required field: {field}")
        elif not post.metadata[field]:
            errors.append(f"Empty required field: {field}")

    return errors

