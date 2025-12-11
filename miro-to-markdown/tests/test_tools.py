"""Tests for Backcasting MCP tools."""

from pathlib import Path

import pytest

from src.mcp_server.tools import BackcastingTools


@pytest.fixture
def repo_root() -> Path:
    """Path to repository root."""
    return Path(__file__).parent.parent.parent


@pytest.fixture
def tools(repo_root: Path) -> BackcastingTools:
    """BackcastingTools instance."""
    return BackcastingTools(repo_root)


class TestGetTemplate:
    """Tests for get_template tool."""

    def test_get_root_cause_template(self, tools: BackcastingTools):
        result = tools.get_template("root_cause")

        assert result["type"] == "backcasting_template"
        assert result["node_type"] == "root_cause"
        assert "frontmatter_schema" in result
        assert "markdown" in result
        assert "---" in result["markdown"]

    def test_get_symptom_template(self, tools: BackcastingTools):
        result = tools.get_template("symptom")

        assert result["node_type"] == "symptom"
        assert "## Description" in result["markdown"]

    def test_get_success_criteria_template(self, tools: BackcastingTools):
        result = tools.get_template("success_criteria")

        assert result["node_type"] == "success_criteria"

    def test_invalid_node_type(self, tools: BackcastingTools):
        with pytest.raises(ValueError, match="Invalid node_type"):
            tools.get_template("invalid_type")


class TestGetNode:
    """Tests for get_node tool."""

    def test_get_root_cause_node(self, tools: BackcastingTools):
        result = tools.get_node("rc-001")

        assert result["type"] == "backcasting_node"
        assert result["id"] == "rc-001"
        assert result["title"] == "Architecture misaligned with modern concerns"
        assert result["node_type"] == "root_cause"
        assert result["path"] == "root_cause/rc-001.md"

    def test_get_symptom_node(self, tools: BackcastingTools):
        result = tools.get_node("rf-001")

        assert result["id"] == "rf-001"
        assert result["node_type"] == "symptom"
        assert result["path"] == "symptom/rf-001.md"

    def test_get_success_criteria_node(self, tools: BackcastingTools):
        result = tools.get_node("sc-001")

        assert result["id"] == "sc-001"
        assert result["node_type"] == "success_criteria"
        assert result["path"] == "success_criteria/sc-001.md"

    def test_node_not_found(self, tools: BackcastingTools):
        with pytest.raises(FileNotFoundError):
            tools.get_node("rc-999")

    def test_invalid_id_prefix(self, tools: BackcastingTools):
        with pytest.raises(ValueError, match="Unrecognized node_id prefix"):
            tools.get_node("invalid-001")

    def test_relations_parsed(self, tools: BackcastingTools):
        result = tools.get_node("rf-001")

        relations = result["relations"]
        assert "rc-006" in relations["triggered_by"]
        assert "rf-012" in relations["triggers"]
        assert "sc-004" in relations["threatens"]


class TestWriteNode:
    """Tests for write_node tool."""

    def test_write_new_node(self, tools: BackcastingTools, tmp_path: Path):
        # Use a temporary directory for testing writes
        temp_tools = BackcastingTools(tmp_path)
        (tmp_path / "root_cause").mkdir()

        markdown = """---
id: rc-999
title: Test Root Cause
type: root_cause
introduced_in_phase:
  - A
triggers: []
tags: [root_cause]
---

## Description
This is a test root cause.
"""
        result = temp_tools.write_node("rc-999", markdown)

        assert result["id"] == "rc-999"
        assert result["title"] == "Test Root Cause"
        assert result["path"] == "root_cause/rc-999.md"

        # Verify file was written
        written_file = tmp_path / "root_cause" / "rc-999.md"
        assert written_file.exists()
        assert "Test Root Cause" in written_file.read_text()

    def test_id_mismatch_raises_error(self, tools: BackcastingTools, tmp_path: Path):
        temp_tools = BackcastingTools(tmp_path)
        (tmp_path / "root_cause").mkdir()

        markdown = """---
id: rc-001
title: Test
type: root_cause
---
"""
        with pytest.raises(ValueError, match="ID mismatch"):
            temp_tools.write_node("rc-999", markdown)

    def test_missing_required_field_raises_error(
        self, tools: BackcastingTools, tmp_path: Path
    ):
        temp_tools = BackcastingTools(tmp_path)

        markdown = """---
id: rc-999
type: root_cause
---
"""
        with pytest.raises(ValueError, match="Missing required field: title"):
            temp_tools.write_node("rc-999", markdown)

    def test_custom_path(self, tools: BackcastingTools, tmp_path: Path):
        temp_tools = BackcastingTools(tmp_path)
        (tmp_path / "custom").mkdir()

        markdown = """---
id: rc-999
title: Test
type: root_cause
---
"""
        result = temp_tools.write_node("rc-999", markdown, path="custom/test.md")

        assert result["path"] == "custom/test.md"
        assert (tmp_path / "custom" / "test.md").exists()

