"""Data models for Backcasting MCP Server."""

from dataclasses import dataclass, field
from typing import Literal

NodeType = Literal["root_cause", "symptom", "success_criteria"]


@dataclass
class FrontmatterSchema:
    """Schema describing required and optional frontmatter fields."""

    required: list[str] = field(default_factory=lambda: ["id", "title", "type"])
    optional: list[str] = field(
        default_factory=lambda: [
            "observed_in_phase",
            "introduced_in_phase",
            "reviewable_in_phase",
            "triggered_by",
            "triggers",
            "leads_from",
            "leads_to",
            "threatens",
            "threatened_by",
            "related_success_criteria",
            "tags",
        ]
    )


@dataclass
class BackcastingTemplate:
    """Template for creating a new Backcasting node."""

    type: str = "backcasting_template"
    node_type: NodeType = "root_cause"
    frontmatter_schema: FrontmatterSchema = field(default_factory=FrontmatterSchema)
    markdown: str = ""


@dataclass
class PhaseInfo:
    """Phase-related information for a node."""

    observed_in_phase: list[str] = field(default_factory=list)
    introduced_in_phase: list[str] = field(default_factory=list)
    reviewable_in_phase: list[str] = field(default_factory=list)


@dataclass
class Relations:
    """Relationship links for a node."""

    leads_from: list[str] = field(default_factory=list)
    triggered_by: list[str] = field(default_factory=list)
    triggers: list[str] = field(default_factory=list)
    leads_to: list[str] = field(default_factory=list)
    threatens: list[str] = field(default_factory=list)
    threatened_by: list[str] = field(default_factory=list)
    related_success_criteria: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass
class BackcastingNode:
    """A single Backcasting node parsed from a Markdown file."""

    type: str = "backcasting_node"
    id: str = ""
    title: str = ""
    node_type: NodeType = "root_cause"
    phase: PhaseInfo = field(default_factory=PhaseInfo)
    relations: Relations = field(default_factory=Relations)
    markdown: str = ""
    path: str = ""


@dataclass
class ChainNode:
    """A lightweight node representation for chain traversal."""

    id: str = ""
    node_type: NodeType = "root_cause"
    title: str = ""


@dataclass
class BackcastingChain:
    """A causal chain from Root Cause to Success Criteria."""

    type: str = "backcasting_chain"
    direction: str = "root_to_success_criteria"
    root_id: str = ""
    nodes: list[ChainNode] = field(default_factory=list)
    paths: list[list[str]] = field(default_factory=list)

