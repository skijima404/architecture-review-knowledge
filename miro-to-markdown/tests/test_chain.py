"""Tests for chain traversal."""

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


class TestGetChainFromRoot:
    """Tests for get_chain_from_root tool."""

    def test_traverses_rc_to_sc(self, tools: BackcastingTools):
        """Test that rc-006 → rf-001 → sc-004 chain is traversed."""
        result = tools.get_chain_from_root("rc-006")

        assert result["type"] == "backcasting_chain"
        assert result["direction"] == "root_to_success_criteria"
        assert result["root_id"] == "rc-006"

        # Check nodes are collected
        node_ids = [n["id"] for n in result["nodes"]]
        assert "rc-006" in node_ids
        assert "rf-001" in node_ids  # triggered by rc-006

        # Check at least one path exists
        assert len(result["paths"]) > 0

    def test_includes_node_metadata(self, tools: BackcastingTools):
        """Test that chain nodes include title and node_type."""
        result = tools.get_chain_from_root("rc-006")

        # Find the rc-006 node
        rc_node = next(n for n in result["nodes"] if n["id"] == "rc-006")
        assert rc_node["title"] == "Unrealistic transition architecture"
        assert rc_node["node_type"] == "root_cause"

    def test_follows_triggers_and_threatens(self, tools: BackcastingTools):
        """Test that both triggers and threatens relationships are followed."""
        result = tools.get_chain_from_root("rc-006")

        node_ids = [n["id"] for n in result["nodes"]]

        # rc-006 triggers rf-001
        assert "rf-001" in node_ids

        # rf-001 threatens sc-004
        assert "sc-004" in node_ids

    def test_handles_multiple_triggers(self, tools: BackcastingTools):
        """Test that nodes with multiple triggers are all followed."""
        result = tools.get_chain_from_root("rc-006")

        node_ids = [n["id"] for n in result["nodes"]]

        # rc-006 triggers both rf-001 and rf-012
        assert "rf-001" in node_ids
        assert "rf-012" in node_ids

    def test_invalid_root_id_prefix(self, tools: BackcastingTools):
        """Test that non-root_cause IDs are rejected."""
        with pytest.raises(ValueError, match="must be a root_cause"):
            tools.get_chain_from_root("rf-001")

    def test_nonexistent_root(self, tools: BackcastingTools):
        """Test that nonexistent root returns empty chain."""
        result = tools.get_chain_from_root("rc-999")

        assert result["root_id"] == "rc-999"
        assert len(result["nodes"]) == 0
        assert len(result["paths"]) == 0

    def test_max_depth_limits_traversal(self, tools: BackcastingTools):
        """Test that max_depth parameter limits traversal."""
        # With max_depth=1, only the root should be visited
        result = tools.get_chain_from_root("rc-006", max_depth=1)

        # Should have limited nodes
        assert len(result["nodes"]) <= 3  # root + immediate children

    def test_avoids_cycles(self, tools: BackcastingTools):
        """Test that cycles are handled (nodes not visited twice)."""
        result = tools.get_chain_from_root("rc-006")

        node_ids = [n["id"] for n in result["nodes"]]
        # No duplicates
        assert len(node_ids) == len(set(node_ids))

    def test_path_contains_valid_sequence(self, tools: BackcastingTools):
        """Test that paths represent valid traversal sequences."""
        result = tools.get_chain_from_root("rc-006")

        for path in result["paths"]:
            # Path should start with the root
            assert path[0] == "rc-006"
            # Path should end with a success_criteria
            assert path[-1].startswith("sc-")


class TestChainWithRealData:
    """Integration tests with real repository data."""

    def test_rc001_chain(self, tools: BackcastingTools):
        """Test chain from rc-001."""
        result = tools.get_chain_from_root("rc-001")

        node_ids = [n["id"] for n in result["nodes"]]
        assert "rc-001" in node_ids
        # rc-001 triggers rf-008
        assert "rf-008" in node_ids

    def test_chain_node_types_are_correct(self, tools: BackcastingTools):
        """Verify node types match their prefixes."""
        result = tools.get_chain_from_root("rc-006")

        for node in result["nodes"]:
            if node["id"].startswith("rc-"):
                assert node["node_type"] == "root_cause"
            elif node["id"].startswith("rf-"):
                assert node["node_type"] == "symptom"
            elif node["id"].startswith("sc-"):
                assert node["node_type"] == "success_criteria"

