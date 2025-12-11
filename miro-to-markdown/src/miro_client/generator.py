"""Markdown file generator from YAML export.

Generates Markdown files from the intermediate YAML export,
creating new files for nodes that don't have existing matches.
"""

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class GeneratorConfig:
    """Configuration for Markdown generation."""

    base_path: Path
    base_path_str: str  # Original string to preserve "./" prefix
    folders: dict[str, str]
    id_prefixes: dict[str, str]

    @classmethod
    def from_yaml(cls, config_path: Path) -> "GeneratorConfig":
        """Load configuration from YAML file.

        Args:
            config_path: Path to config.yaml

        Returns:
            GeneratorConfig instance
        """
        with open(config_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)

        output = config.get("output", {})
        base_path_str = output.get("base_path", "..")
        base_path = Path(base_path_str)

        folders = output.get("folders", {
            "success_criteria": "success_criteria",
            "symptom": "symptom",
            "root_cause": "root_cause",
        })

        id_prefixes = config.get("id_prefixes", {
            "success_criteria": "sc",
            "symptom": "rf",
            "root_cause": "rc",
        })

        return cls(
            base_path=base_path,
            base_path_str=base_path_str,
            folders=folders,
            id_prefixes=id_prefixes,
        )

    def get_output_folder(
        self,
        node_type: str,
        repo_root: Path,
        miro_root: Path | None = None,
    ) -> Path:
        """Get the output folder for a node type.

        Args:
            node_type: Node type (success_criteria, symptom, root_cause)
            repo_root: Repository root path
            miro_root: miro-to-markdown folder path (for relative paths starting with ./)

        Returns:
            Path to the output folder
        """
        folder_name = self.folders.get(node_type, node_type)
        if self.base_path.is_absolute():
            return self.base_path / folder_name
        elif self.base_path_str.startswith("./") and miro_root:
            # Relative to miro-to-markdown folder (starts with ./)
            return (miro_root / self.base_path / folder_name).resolve()
        else:
            # Relative to repo root (e.g., ".." means repo root)
            return (repo_root / self.base_path / folder_name).resolve()


def generate_frontmatter(node: dict, node_type: str) -> str:
    """Generate YAML frontmatter for a node.

    Args:
        node: Node data from YAML export
        node_type: Node type

    Returns:
        YAML frontmatter string
    """
    lines = ["---"]
    lines.append(f"id: {node['id']}")
    lines.append(f"title: {node['title']}")
    lines.append(f"type: {node_type}")

    # Phase fields
    if node_type == "root_cause":
        phase = node.get("introduced_in_phase", [])
        if phase:
            lines.append("introduced_in_phase:")
            for p in phase:
                lines.append(f"  - {p}")
        lines.append("reviewable_in_phase: []")
    else:
        phase = node.get("observed_in_phase", [])
        if phase:
            lines.append("observed_in_phase:")
            for p in phase:
                lines.append(f"  - {p}")

    # Relationship fields based on node type
    edges = node.get("edges", {})

    if node_type == "success_criteria":
        # SC has: threatened_by
        threatened_by = edges.get("threatened_by", [])
        if threatened_by:
            lines.append("threatened_by:")
            for target in threatened_by:
                lines.append(f'  - "[[{target}]]"')
        else:
            lines.append("threatened_by: []")

    elif node_type == "symptom":
        # Symptom has: triggered_by, triggers, threatens
        triggered_by = edges.get("triggered_by", [])
        if triggered_by:
            lines.append("triggered_by:")
            for target in triggered_by:
                lines.append(f'  - "[[{target}]]"')
        else:
            lines.append("triggered_by: []")

        triggers = edges.get("triggers", [])
        if triggers:
            lines.append("triggers:")
            for target in triggers:
                lines.append(f'  - "[[{target}]]"')
        else:
            lines.append("triggers: []")

        threatens = edges.get("threatens", [])
        if threatens:
            lines.append("threatens:")
            for target in threatens:
                lines.append(f'  - "[[{target}]]"')
        else:
            lines.append("threatens: []")

    elif node_type == "root_cause":
        # RC has: leads_from, triggers, leads_to
        leads_from = edges.get("leads_from", [])
        if leads_from:
            lines.append("leads_from:")
            for target in leads_from:
                lines.append(f'  - "[[{target}]]"')
        else:
            lines.append("leads_from: []")

        triggers = edges.get("triggers", [])
        if triggers:
            lines.append("triggers:")
            for target in triggers:
                lines.append(f'  - "[[{target}]]"')
        else:
            lines.append("triggers: []")

        leads_to = edges.get("leads_to", [])
        if leads_to:
            lines.append("leads_to:")
            for target in leads_to:
                lines.append(f'  - "[[{target}]]"')
        else:
            lines.append("leads_to: []")

    # Tags
    lines.append(f"tags: [{node_type}]")
    lines.append("---")

    return "\n".join(lines)


def generate_body(node_type: str) -> str:
    """Generate body template for a node type.

    Args:
        node_type: Node type

    Returns:
        Markdown body template
    """
    if node_type == "success_criteria":
        return """
## Description
TBD

## Rationale
TBD
"""
    elif node_type == "symptom":
        return """
## Description
TBD

## Context
TBD

## Severity
TBD
"""
    elif node_type == "root_cause":
        return """
## Description
TBD

## Context
TBD

## Impact
TBD

## Preventive Measures
TBD
"""
    else:
        return "\n## Description\nTBD\n"


def generate_markdown(node: dict, node_type: str) -> str:
    """Generate complete Markdown content for a node.

    Args:
        node: Node data from YAML export
        node_type: Node type

    Returns:
        Complete Markdown content
    """
    frontmatter = generate_frontmatter(node, node_type)
    body = generate_body(node_type)
    return frontmatter + body


def resolve_miro_ids_to_node_ids(
    nodes_by_type: dict[str, list[dict]],
) -> dict[str, str]:
    """Build mapping from miro_id to node_id.

    Args:
        nodes_by_type: Dict of node_type -> list of nodes

    Returns:
        Dict mapping miro_id -> node_id
    """
    mapping = {}
    for nodes in nodes_by_type.values():
        for node in nodes:
            miro_id = node.get("miro_id")
            node_id = node.get("existing_match") or node.get("id")
            if miro_id and node_id:
                mapping[miro_id] = node_id
    return mapping


def convert_edges_to_node_ids(
    node: dict,
    miro_to_node: dict[str, str],
) -> dict:
    """Convert edge miro_ids to node_ids.

    Args:
        node: Node data with edges containing miro_ids
        miro_to_node: Mapping from miro_id to node_id

    Returns:
        Node with edges converted to node_ids
    """
    result = dict(node)
    edges = node.get("edges", {})
    converted_edges = {}

    for edge_type, targets in edges.items():
        converted = []
        for target in targets:
            node_id = miro_to_node.get(target)
            if node_id:
                converted.append(node_id)
        if converted:
            converted_edges[edge_type] = converted

    result["edges"] = converted_edges
    return result


@dataclass
class GenerationResult:
    """Result of Markdown generation."""

    created: list[Path]
    skipped: list[str]  # Nodes with existing matches


def generate_all(
    yaml_path: Path,
    config: GeneratorConfig,
    repo_root: Path,
    miro_root: Path | None = None,
    dry_run: bool = False,
) -> GenerationResult:
    """Generate Markdown files from YAML export.

    Args:
        yaml_path: Path to the YAML export file
        config: Generator configuration
        repo_root: Repository root path
        miro_root: miro-to-markdown folder path
        dry_run: If True, don't actually write files

    Returns:
        GenerationResult with created and skipped files
    """
    with open(yaml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # Build miro_id -> node_id mapping
    nodes_by_type = {
        "success_criteria": data.get("success_criteria", []),
        "symptom": data.get("symptom", []),
        "root_cause": data.get("root_cause", []),
    }
    miro_to_node = resolve_miro_ids_to_node_ids(nodes_by_type)

    created: list[Path] = []
    skipped: list[str] = []

    for node_type, nodes in nodes_by_type.items():
        output_folder = config.get_output_folder(node_type, repo_root, miro_root)

        for node in nodes:
            # Skip if node already exists
            if node.get("existing_match"):
                skipped.append(node["existing_match"])
                continue

            # Convert edges from miro_ids to node_ids
            node_with_ids = convert_edges_to_node_ids(node, miro_to_node)

            # Generate Markdown content
            content = generate_markdown(node_with_ids, node_type)

            # Determine output path
            node_id = node["id"]
            output_path = output_folder / f"{node_id}.md"

            if not dry_run:
                # Ensure folder exists
                output_folder.mkdir(parents=True, exist_ok=True)

                # Write file
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(content)

            created.append(output_path)

    return GenerationResult(created=created, skipped=skipped)

