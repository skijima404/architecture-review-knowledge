"""Tests for frontmatter parsing."""

from pathlib import Path

import pytest

from src.mcp_server.parser import extract_ids_from_wikilinks, parse_node, parse_template


class TestExtractIdsFromWikilinks:
    """Tests for wikilink extraction."""

    def test_extracts_single_id(self):
        result = extract_ids_from_wikilinks(["[[rc-001]]"])
        assert result == ["rc-001"]

    def test_extracts_multiple_ids(self):
        result = extract_ids_from_wikilinks(["[[rc-001]]", "[[rf-002]]", "[[sc-003]]"])
        assert result == ["rc-001", "rf-002", "sc-003"]

    def test_handles_empty_list(self):
        result = extract_ids_from_wikilinks([])
        assert result == []

    def test_handles_none(self):
        result = extract_ids_from_wikilinks(None)
        assert result == []

    def test_handles_plain_ids(self):
        """IDs without wikilink syntax should be returned as-is."""
        result = extract_ids_from_wikilinks(["rc-001", "rf-002"])
        assert result == ["rc-001", "rf-002"]

    def test_handles_mixed_formats(self):
        result = extract_ids_from_wikilinks(["[[rc-001]]", "rf-002"])
        assert result == ["rc-001", "rf-002"]


class TestParseTemplate:
    """Tests for template parsing."""

    @pytest.fixture
    def templates_dir(self) -> Path:
        """Path to templates directory."""
        return Path(__file__).parent.parent.parent / "templates"

    def test_parse_root_cause_template(self, templates_dir: Path):
        template = parse_template(templates_dir / "root_cause.md")

        assert template.type == "backcasting_template"
        assert template.node_type == "root_cause"
        assert "id" in template.frontmatter_schema.required
        assert "title" in template.frontmatter_schema.required
        assert "type" in template.frontmatter_schema.required
        assert "---" in template.markdown

    def test_parse_symptom_template(self, templates_dir: Path):
        template = parse_template(templates_dir / "symptom.md")

        assert template.node_type == "symptom"
        assert "## Description" in template.markdown

    def test_parse_success_criteria_template(self, templates_dir: Path):
        template = parse_template(templates_dir / "success_criteria.md")

        assert template.node_type == "success_criteria"


class TestParseNode:
    """Tests for node parsing."""

    @pytest.fixture
    def repo_root(self) -> Path:
        """Path to repository root."""
        return Path(__file__).parent.parent.parent

    def test_parse_root_cause_node(self, repo_root: Path):
        node = parse_node(repo_root / "root_cause" / "rc-001.md")

        assert node.type == "backcasting_node"
        assert node.id == "rc-001"
        assert node.title == "Architecture misaligned with modern concerns"
        assert node.node_type == "root_cause"
        assert "C" in node.phase.introduced_in_phase
        assert "D" in node.phase.reviewable_in_phase
        assert "rf-008" in node.relations.triggers
        assert "root_cause" in node.relations.tags

    def test_parse_symptom_node(self, repo_root: Path):
        node = parse_node(repo_root / "symptom" / "rf-001.md")

        assert node.id == "rf-001"
        assert node.title == "Repeated delays"
        assert node.node_type == "symptom"
        assert "G" in node.phase.observed_in_phase
        assert "rc-006" in node.relations.triggered_by
        assert "rf-012" in node.relations.triggers
        assert "sc-004" in node.relations.threatens

    def test_parse_success_criteria_node(self, repo_root: Path):
        node = parse_node(repo_root / "success_criteria" / "sc-001.md")

        assert node.id == "sc-001"
        assert node.title == "Realization of Business Outcomes"
        assert node.node_type == "success_criteria"
        assert "rf-009" in node.relations.threatened_by

    def test_markdown_content_preserved(self, repo_root: Path):
        node = parse_node(repo_root / "root_cause" / "rc-001.md")

        assert "---" in node.markdown
        assert "## Description" in node.markdown
        assert "アーキテクチャ" in node.markdown

