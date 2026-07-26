# Miro to Failure Model

This tool converts a Miro Backcasting Map into the repository's curated Failure
Model Markdown.

It is an authoring adapter. Canonical node and board contracts live outside the
tool:

- `../../schemas/failure-model/node-spec.md`
- `../../schemas/failure-model/miro-board-rules.md`
- `../../schemas/failure-model/miro-mapping-spec.md`

The tool does not provide MCP or RAG functionality.

## Setup

```bash
cd tooling/miro-to-failure-model
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,miro]"
```

Create a local `.env`:

```text
MIRO_ACCESS_TOKEN=your_access_token_here
MIRO_BOARD_ID=your_board_id_here
```

## Repository Configuration

The checked-in `config.yaml` reads and writes the canonical Failure Model:

```yaml
output:
  base_path: "."
  folders:
    success_criteria: "knowledge/curated/failure-model/success-criteria"
    symptom: "knowledge/curated/failure-model/symptoms"
    root_cause: "knowledge/curated/failure-model/root-causes"
```

For isolated testing, create `config.local.yaml` with a tool-relative path:

```yaml
output:
  base_path: "./test_output"
  folders:
    success_criteria: "success-criteria"
    symptom: "symptoms"
    root_cause: "root-causes"
```

## Workflow

```text
Miro export -> Diff review -> Apply existing changes or generate new nodes
```

### 1. Export

```bash
python -m src.miro_client.cli
```

Produces `output/node_list.yaml`.

### 2. Generate a diff

```bash
python -m src.miro_client.diff_cli
```

Produces `output/diff_report.yaml`.

### 3. Apply reviewed changes

```bash
python -m src.miro_client.apply_diff --dry-run
python -m src.miro_client.apply_diff
```

### 4. Generate new nodes

```bash
python -m src.miro_client.generate_cli --dry-run
python -m src.miro_client.generate_cli
```

## Tests

```bash
python -m pytest
python -m ruff check src tests scripts
```

The generated output directory and tests are not Production knowledge sources.
