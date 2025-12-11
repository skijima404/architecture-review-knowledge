# Miro to Markdown Converter

A tool to convert Backcasting Maps from Miro boards into Markdown files.

## Setup

### 1. Environment Setup

```bash
cd miro-to-markdown

# Create Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev,miro]"
```

### 2. Environment Variables

Create a `.env` file:

```
MIRO_ACCESS_TOKEN=your_access_token_here
MIRO_BOARD_ID=your_board_id_here
```

- **Access Token**: Obtain from [Miro Developer Portal](https://miro.com/app/settings/user-profile/apps)
- **Board ID**: Extract from Miro board URL (e.g., `https://miro.com/app/board/uXjVGfVHJzc=/` → `uXjVGfVHJzc=`)

### 3. Configuration File (Optional)

For testing with a separate output directory, create `config.local.yaml`:

```yaml
output:
  base_path: "./test_output"  # Test folder within miro-to-markdown

  folders:
    success_criteria: "success_criteria"
    symptom: "symptom"
    root_cause: "root_cause"
```

For production (output to repository root), use `config.yaml` as-is:

```yaml
output:
  base_path: ".."  # Repository root
```

---

## Usage

### Workflow Overview

```
1. Miro Export  →  2. Diff Check  →  3. Apply/Generate
   (Generate YAML)   (Review diff)     (Update Markdown)
```

### Step 1: Export from Miro

```bash
python -m src.miro_client.cli
```

Output: `output/node_list.yaml`

- Fetches sticky notes and connectors from Miro
- Matches with existing Markdown files
- Auto-detects edges (relationships) and TOGAF phases

### Step 2: Generate Diff Report

```bash
python -m src.miro_client.diff_cli
```

Output: `output/diff_report.yaml`

- Detects differences with existing files
- Edge additions/removals
- Phase changes

### Step 3a: Apply Diff (Update Existing Files)

```bash
# Preview changes
python -m src.miro_client.apply_diff --dry-run

# Apply changes
python -m src.miro_client.apply_diff
```

### Step 3b: Generate New Markdown Files

```bash
# Preview
python -m src.miro_client.generate_cli --dry-run

# Generate
python -m src.miro_client.generate_cli
```

- Skips nodes that already have existing files
- Only generates new nodes

---

## CLI Options

### `cli.py` (Miro Export)

```bash
python -m src.miro_client.cli [OPTIONS]

Options:
  --board-id TEXT    Miro board ID (default: MIRO_BOARD_ID from .env)
  --output, -o TEXT  Output file (default: output/node_list.yaml)
  --config, -c TEXT  Config file (default: config.yaml)
```

### `diff_cli.py` (Diff Report)

```bash
python -m src.miro_client.diff_cli [OPTIONS]

Options:
  --input, -i TEXT   Input YAML (default: output/node_list.yaml)
  --output, -o TEXT  Output file (default: output/diff_report.yaml)
  --config, -c TEXT  Config file (default: config.yaml)
```

### `apply_diff.py` (Apply Diff)

```bash
python -m src.miro_client.apply_diff [OPTIONS]

Options:
  --input, -i TEXT   Diff file (default: output/diff_report.yaml)
  --dry-run          Preview without making changes
```

### `generate_cli.py` (Markdown Generation)

```bash
python -m src.miro_client.generate_cli [OPTIONS]

Options:
  --input, -i TEXT   Input YAML (default: output/node_list.yaml)
  --config, -c TEXT  Config file (default: config.yaml)
  --dry-run          Preview without generating files
```

---

## Miro Board Rules

See [docs/miro-board-rules.md](docs/miro-board-rules.md) for details.

### Sticky Note Colors → Node Types

| Color | Node Type |
|-------|-----------|
| 🔴 Red | Success Criteria |
| 🟡 Light Yellow | Symptom |
| 🔵 Light Blue | Root Cause |
| ⬜ Gray | Ignored (for labels) |

### Connectors → Relationships

- **Cross-type connections**: Direction auto-inferred from causal flow
  - RC → SYM = `triggers`
  - SYM → SC = `threatens`
- **Same-type connections**: Direction determined by X position
  - Left → Right = `leads_to`
  - Right → Left = `leads_from`

### Phase Detection

- Auto-detected from Phase header shapes (A, B-D, E, F, G, H)
- Sticky note's X position determines its phase

---

## Testing

```bash
# Run all tests
python -m pytest

# Run specific tests
python -m pytest tests/test_miro_matcher.py -v
```

---

## Documentation

- [Markdown Node Specification](docs/backcasting-map-spec.md)
- [Miro Board Rules](docs/miro-board-rules.md)
- [MCP Server Specification](docs/backcasting-mcp-spec.md)
