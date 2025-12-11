"""TOGAF Phase detection based on Miro board layout.

Detects which TOGAF phase a sticky note belongs to by comparing its
X position with phase header shapes (A, B-D, E, F, G) on the board.
"""

import re
from dataclasses import dataclass

import requests


@dataclass
class PhaseRange:
    """Represents a TOGAF phase and its X-axis range on the board."""

    phase: str  # e.g., "A", "B-D", "E", "F", "G"
    x_min: float
    x_max: float


def fetch_phase_headers(
    board_id: str,
    access_token: str,
) -> list[dict]:
    """Fetch shape items that represent phase headers.

    Args:
        board_id: Miro board ID
        access_token: Miro API access token

    Returns:
        List of shape items with phase labels
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    shapes = []
    cursor = None

    while True:
        params = {"limit": 50, "type": "shape"}
        if cursor:
            params["cursor"] = cursor

        response = requests.get(
            f"https://api.miro.com/v2/boards/{board_id}/items",
            headers=headers,
            params=params,
        )
        response.raise_for_status()
        data = response.json()

        for item in data.get("data", []):
            if item.get("type") == "shape":
                shapes.append(item)

        cursor = data.get("cursor")
        if not cursor:
            break

    return shapes


def parse_phase_label(content: str) -> str | None:
    """Extract phase label from shape content.

    Args:
        content: HTML content like "<p>A</p>" or "<p>B-D</p>"

    Returns:
        Phase label (A, B-D, E, F, G) or None if not a phase header
    """
    if not content:
        return None

    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", content).strip()

    # Check if it's a valid phase label
    valid_phases = {"A", "B-D", "E", "F", "G", "H"}
    if text in valid_phases:
        return text

    return None


def calculate_phase_ranges(shapes: list[dict]) -> list[PhaseRange]:
    """Calculate X-axis ranges for each phase based on header shapes.

    Assumes phase headers are arranged horizontally with non-overlapping ranges.
    If multiple shapes have the same phase label, only the leftmost one is used.

    Args:
        shapes: List of shape items from Miro API

    Returns:
        List of PhaseRange objects sorted by x_min
    """
    # Collect all phase shapes
    phase_shapes_raw = []

    for shape in shapes:
        content = shape.get("data", {}).get("content", "")
        phase = parse_phase_label(content)

        if phase:
            position = shape.get("position", {})
            geometry = shape.get("geometry", {})

            x = position.get("x", 0)
            width = geometry.get("width", 0)

            # Shape position is center, calculate edges
            x_min = x - width / 2
            x_max = x + width / 2

            phase_shapes_raw.append({
                "phase": phase,
                "x_center": x,
                "x_min": x_min,
                "x_max": x_max,
            })

    # Deduplicate: keep only the leftmost shape for each phase
    phase_shapes = []
    seen_phases: set[str] = set()
    for ps in sorted(phase_shapes_raw, key=lambda p: p["x_center"]):
        if ps["phase"] not in seen_phases:
            phase_shapes.append(ps)
            seen_phases.add(ps["phase"])

    # Sort by x position
    phase_shapes.sort(key=lambda p: p["x_center"])

    # Calculate ranges with midpoints between adjacent phases
    ranges = []
    for i, ps in enumerate(phase_shapes):
        # For the first phase, extend to negative infinity
        if i == 0:
            range_min = float("-inf")
        else:
            # Midpoint between this phase and previous
            prev = phase_shapes[i - 1]
            range_min = (prev["x_max"] + ps["x_min"]) / 2

        # For the last phase, extend to positive infinity
        if i == len(phase_shapes) - 1:
            range_max = float("inf")
        else:
            # Midpoint between this phase and next
            next_ps = phase_shapes[i + 1]
            range_max = (ps["x_max"] + next_ps["x_min"]) / 2

        ranges.append(PhaseRange(
            phase=ps["phase"],
            x_min=range_min,
            x_max=range_max,
        ))

    return ranges


def detect_phase(x: float, phase_ranges: list[PhaseRange]) -> str | None:
    """Detect which phase a position belongs to.

    Args:
        x: X coordinate of the item
        phase_ranges: List of PhaseRange objects

    Returns:
        Phase label (e.g., "A", "B-D") or None if not in any phase
    """
    for pr in phase_ranges:
        if pr.x_min <= x < pr.x_max:
            return pr.phase
    return None


def expand_phase(phase: str) -> list[str]:
    """Expand phase label to list format.

    B-D is expanded to ["B", "C", "D"] for clarity, as the combined
    notation is practical but less intuitive for those unfamiliar
    with TOGAF iteration patterns.

    Args:
        phase: Phase label (e.g., "A", "B-D")

    Returns:
        List of phase labels (e.g., ["A"], ["B", "C", "D"])
    """
    if phase == "B-D":
        return ["B", "C", "D"]
    return [phase]


class PhaseDetector:
    """Detects TOGAF phase for nodes based on their position."""

    def __init__(self, board_id: str, access_token: str):
        """Initialize the phase detector.

        Args:
            board_id: Miro board ID
            access_token: Miro API access token
        """
        self.board_id = board_id
        self.access_token = access_token
        self._phase_ranges: list[PhaseRange] | None = None

    def _load_phase_ranges(self) -> None:
        """Load phase ranges from Miro board."""
        shapes = fetch_phase_headers(self.board_id, self.access_token)
        self._phase_ranges = calculate_phase_ranges(shapes)

    @property
    def phase_ranges(self) -> list[PhaseRange]:
        """Get phase ranges, loading from API if needed."""
        if self._phase_ranges is None:
            self._load_phase_ranges()
        return self._phase_ranges

    def detect(self, x: float) -> list[str] | None:
        """Detect phase(s) for a given X position.

        Args:
            x: X coordinate

        Returns:
            List of phase labels, or None if not in any phase
        """
        phase = detect_phase(x, self.phase_ranges)
        if phase:
            return expand_phase(phase)
        return None

    def get_phase_field(self, node_type: str) -> str:
        """Get the appropriate phase field name for a node type.

        Args:
            node_type: Node type (root_cause, symptom, success_criteria)

        Returns:
            Field name (introduced_in_phase, observed_in_phase, etc.)
        """
        if node_type == "root_cause":
            return "introduced_in_phase"
        elif node_type == "symptom":
            return "observed_in_phase"
        elif node_type == "success_criteria":
            return "observed_in_phase"  # SC is also observed
        else:
            return "phase"  # Fallback

