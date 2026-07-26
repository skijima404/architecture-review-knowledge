"""Tests for safe Failure Model generation."""

from pathlib import Path

import yaml

from src.miro_client.cli import get_repo_root
from src.miro_client.generator import GeneratorConfig, generate_all


def write_export(path: Path, node_id: str) -> None:
    data = {
        "success_criteria": [],
        "symptom": [],
        "root_cause": [
            {
                "id": node_id,
                "title": "Generated root cause",
                "miro_id": "miro-1",
                "edges": {},
            }
        ],
    }
    path.write_text(yaml.safe_dump(data), encoding="utf-8")


def test_repo_root_resolves_after_tool_move():
    repo_root = get_repo_root()

    assert (repo_root / "knowledge/curated/failure-model").is_dir()
    assert (repo_root / "docs/traceability/registry.md").is_file()


def test_generate_skips_existing_file_even_without_existing_match(tmp_path: Path):
    output_dir = tmp_path / "root-causes"
    output_dir.mkdir()
    existing = output_dir / "rc-001.md"
    existing.write_text("existing content", encoding="utf-8")

    yaml_path = tmp_path / "nodes.yaml"
    write_export(yaml_path, "rc-001")

    config = GeneratorConfig(
        base_path=Path("."),
        base_path_str=".",
        folders={"root_cause": "root-causes"},
        id_prefixes={"root_cause": "rc"},
    )

    result = generate_all(
        yaml_path=yaml_path,
        config=config,
        repo_root=tmp_path,
        dry_run=False,
    )

    assert result.created == []
    assert result.skipped == ["rc-001"]
    assert existing.read_text(encoding="utf-8") == "existing content"


def test_generate_creates_new_file_in_configured_folder(tmp_path: Path):
    yaml_path = tmp_path / "nodes.yaml"
    write_export(yaml_path, "rc-999")

    config = GeneratorConfig(
        base_path=Path("."),
        base_path_str=".",
        folders={"root_cause": "root-causes"},
        id_prefixes={"root_cause": "rc"},
    )

    result = generate_all(
        yaml_path=yaml_path,
        config=config,
        repo_root=tmp_path,
        dry_run=False,
    )

    expected = tmp_path / "root-causes/rc-999.md"
    assert result.created == [expected]
    assert result.skipped == []
    assert expected.is_file()
