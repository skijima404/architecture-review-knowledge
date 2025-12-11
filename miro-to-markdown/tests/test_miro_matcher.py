"""Tests for existing node matching."""

from pathlib import Path

import pytest

from src.miro_client.matcher import (
    ExistingNode,
    NodeMatcher,
    find_matching_node,
    get_next_id,
    normalize_title,
)


class TestNormalizeTitle:
    """Tests for title normalization."""

    def test_lowercases(self):
        assert normalize_title("Hello World") == "hello world"

    def test_normalizes_whitespace(self):
        assert normalize_title("  Multiple   spaces  ") == "multiple spaces"

    def test_handles_empty(self):
        assert normalize_title("") == ""


class TestFindMatchingNode:
    """Tests for finding matching nodes."""

    @pytest.fixture
    def existing_nodes(self) -> list[ExistingNode]:
        return [
            ExistingNode("rc-001", "Test Root Cause", "root_cause", Path("rc-001.md")),
            ExistingNode("rf-001", "Test Symptom", "symptom", Path("rf-001.md")),
            ExistingNode("sc-001", "Test Success", "success_criteria", Path("sc-001.md")),
        ]

    def test_finds_exact_match(self, existing_nodes):
        result = find_matching_node("Test Root Cause", "root_cause", existing_nodes)

        assert result is not None
        assert result.id == "rc-001"

    def test_finds_case_insensitive_match(self, existing_nodes):
        result = find_matching_node("TEST ROOT CAUSE", "root_cause", existing_nodes)

        assert result is not None
        assert result.id == "rc-001"

    def test_requires_matching_type(self, existing_nodes):
        # Same title but wrong type
        result = find_matching_node("Test Root Cause", "symptom", existing_nodes)

        assert result is None

    def test_returns_none_for_no_match(self, existing_nodes):
        result = find_matching_node("Unknown Title", "root_cause", existing_nodes)

        assert result is None


class TestGetNextId:
    """Tests for ID generation."""

    def test_generates_next_id(self):
        existing = [
            ExistingNode("rc-001", "A", "root_cause", Path("a.md")),
            ExistingNode("rc-002", "B", "root_cause", Path("b.md")),
            ExistingNode("rc-005", "C", "root_cause", Path("c.md")),
        ]
        result = get_next_id("rc", existing)

        assert result == "rc-006"

    def test_starts_at_001_when_empty(self):
        result = get_next_id("rc", [])

        assert result == "rc-001"

    def test_ignores_other_prefixes(self):
        existing = [
            ExistingNode("rf-010", "A", "symptom", Path("a.md")),
        ]
        result = get_next_id("rc", existing)

        assert result == "rc-001"


class TestNodeMatcher:
    """Tests for NodeMatcher class."""

    @pytest.fixture
    def repo_root(self) -> Path:
        """Path to repository root."""
        return Path(__file__).parent.parent.parent

    def test_loads_existing_nodes(self, repo_root):
        matcher = NodeMatcher(repo_root)

        # Should have loaded nodes from rc-001, rf-001, sc-001, etc.
        assert len(matcher.existing_nodes) > 0

    def test_matches_existing_node(self, repo_root):
        matcher = NodeMatcher(repo_root)

        # This should match an existing node
        assigned_id, existing_match = matcher.match_or_generate_id(
            "Repeated delays",
            "symptom",
            "rf",
        )

        # rf-001 has title "Repeated delays"
        assert existing_match == "rf-001"
        assert assigned_id == "rf-001"

    def test_generates_new_id_for_unknown(self, repo_root):
        matcher = NodeMatcher(repo_root)

        assigned_id, existing_match = matcher.match_or_generate_id(
            "Brand New Node That Does Not Exist",
            "root_cause",
            "rc",
        )

        assert existing_match is None
        assert assigned_id.startswith("rc-")

