"""Tests for Miro node mapping."""

import pytest

from src.miro_client.api import MiroStickyNote
from src.miro_client.mapper import (
    get_node_type,
    is_excluded_title,
    map_all_sticky_notes,
    map_sticky_note,
    strip_html_tags,
)


class TestStripHtmlTags:
    """Tests for HTML tag stripping."""

    def test_removes_paragraph_tags(self):
        assert strip_html_tags("<p>Hello World</p>") == "Hello World"

    def test_removes_nested_tags(self):
        assert strip_html_tags("<p><strong>Bold</strong> text</p>") == "Bold text"

    def test_handles_no_tags(self):
        assert strip_html_tags("Plain text") == "Plain text"

    def test_normalizes_whitespace(self):
        assert strip_html_tags("  Multiple   spaces  ") == "Multiple spaces"

    def test_handles_empty_string(self):
        assert strip_html_tags("") == ""


class TestIsExcludedTitle:
    """Tests for excluded title detection."""

    def test_excludes_success_criteria(self):
        assert is_excluded_title("Success Criteria") is True

    def test_excludes_symptom(self):
        assert is_excluded_title("Symptom") is True

    def test_excludes_root_cause(self):
        assert is_excluded_title("Root Cause") is True

    def test_case_insensitive(self):
        assert is_excluded_title("SUCCESS CRITERIA") is True
        assert is_excluded_title("root cause") is True

    def test_allows_normal_titles(self):
        assert is_excluded_title("Design-induced operational risk") is False
        assert is_excluded_title("Compliance with Architecture Principles") is False


class TestGetNodeType:
    """Tests for color to node type mapping."""

    def test_red_is_success_criteria(self):
        assert get_node_type("red") == "success_criteria"

    def test_light_yellow_is_symptom(self):
        assert get_node_type("light_yellow") == "symptom"

    def test_light_blue_is_root_cause(self):
        assert get_node_type("light_blue") == "root_cause"

    def test_gray_is_ignored(self):
        assert get_node_type("gray") is None

    def test_unknown_color_is_ignored(self):
        assert get_node_type("purple") is None


class TestMapStickyNote:
    """Tests for mapping individual sticky notes."""

    def test_maps_red_to_success_criteria(self):
        note = MiroStickyNote(
            miro_id="123",
            content="<p>Test Success Criteria</p>",
            fill_color="red",
        )
        result = map_sticky_note(note)

        assert result is not None
        assert result.node_type == "success_criteria"
        assert result.id_prefix == "sc"
        assert result.title == "Test Success Criteria"

    def test_maps_light_yellow_to_symptom(self):
        note = MiroStickyNote(
            miro_id="456",
            content="<p>Test Symptom</p>",
            fill_color="light_yellow",
        )
        result = map_sticky_note(note)

        assert result is not None
        assert result.node_type == "symptom"
        assert result.id_prefix == "rf"

    def test_maps_light_blue_to_root_cause(self):
        note = MiroStickyNote(
            miro_id="789",
            content="<p>Test Root Cause</p>",
            fill_color="light_blue",
        )
        result = map_sticky_note(note)

        assert result is not None
        assert result.node_type == "root_cause"
        assert result.id_prefix == "rc"

    def test_ignores_gray_notes(self):
        note = MiroStickyNote(
            miro_id="999",
            content="<p>Gray Memo</p>",
            fill_color="gray",
        )
        result = map_sticky_note(note)

        assert result is None

    def test_ignores_empty_content(self):
        note = MiroStickyNote(
            miro_id="111",
            content="",
            fill_color="red",
        )
        result = map_sticky_note(note)

        assert result is None

    def test_ignores_header_labels(self):
        """Header labels like 'Success Criteria' should be excluded."""
        note = MiroStickyNote(
            miro_id="222",
            content="<p>Success Criteria</p>",
            fill_color="red",
        )
        result = map_sticky_note(note)

        assert result is None

    def test_preserves_position(self):
        note = MiroStickyNote(
            miro_id="222",
            content="<p>Positioned</p>",
            fill_color="red",
            position_x=100.5,
            position_y=200.5,
        )
        result = map_sticky_note(note)

        assert result is not None
        assert result.position_x == 100.5
        assert result.position_y == 200.5


class TestMapAllStickyNotes:
    """Tests for mapping multiple sticky notes."""

    def test_filters_out_ignored_colors(self):
        notes = [
            MiroStickyNote("1", "<p>SC</p>", "red"),
            MiroStickyNote("2", "<p>Memo</p>", "gray"),
            MiroStickyNote("3", "<p>RC</p>", "light_blue"),
        ]
        result = map_all_sticky_notes(notes)

        assert len(result) == 2
        assert result[0].node_type == "success_criteria"
        assert result[1].node_type == "root_cause"

    def test_handles_empty_list(self):
        result = map_all_sticky_notes([])
        assert result == []

