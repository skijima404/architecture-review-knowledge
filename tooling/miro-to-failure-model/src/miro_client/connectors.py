"""Miro connector (edge) extraction and processing.

Extracts relationships between sticky notes from Miro connectors.
"""

import os
from dataclasses import dataclass, field

import requests
from dotenv import load_dotenv


@dataclass
class MiroConnector:
    """Represents a connector (line) from Miro board."""

    connector_id: str
    start_item_id: str | None
    end_item_id: str | None
    start_x: float | None = None
    start_y: float | None = None
    end_x: float | None = None
    end_y: float | None = None
    stroke_style: str | None = None


@dataclass
class Edge:
    """Represents a relationship edge between nodes."""

    from_miro_id: str
    to_miro_id: str
    edge_type: str  # triggers, threatens, leads_to, etc.
    connector_id: str


@dataclass
class EdgeWarning:
    """Warning for problematic connectors."""

    connector_id: str
    warning_type: str  # disconnected, unknown_edge_type
    details: dict = field(default_factory=dict)


# Edge type mapping based on node types and direction
# (from_type, to_type, direction) -> edge_label
EDGE_TYPE_MAP: dict[tuple[str, str, str], str] = {
    # Forward (right direction): triggers, threatens, leads_to
    ("root_cause", "symptom", "forward"): "triggers",
    ("symptom", "success_criteria", "forward"): "threatens",
    ("root_cause", "root_cause", "forward"): "leads_to",
    ("symptom", "symptom", "forward"): "triggers",
    # Backward (left direction): triggered_by, threatened_by, leads_from
    ("root_cause", "symptom", "backward"): "triggered_by",
    ("symptom", "success_criteria", "backward"): "threatened_by",
    ("root_cause", "root_cause", "backward"): "leads_from",
    ("symptom", "symptom", "backward"): "triggered_by",
}

# For cross-type edges, we can auto-infer direction based on node types
# The "natural" direction is always cause → effect
CROSS_TYPE_NATURAL_DIRECTION: dict[tuple[str, str], str] = {
    ("root_cause", "symptom"): "forward",  # RC causes SYM
    ("symptom", "root_cause"): "backward",  # SYM is caused by RC
    ("symptom", "success_criteria"): "forward",  # SYM threatens SC
    ("success_criteria", "symptom"): "backward",  # SC is threatened by SYM
}


def fetch_connectors(board_id: str, access_token: str | None = None) -> list[MiroConnector]:
    """Fetch all connectors from a Miro board.

    Args:
        board_id: Miro board ID
        access_token: Optional access token (reads from env if not provided)

    Returns:
        List of MiroConnector objects
    """
    load_dotenv()
    token = access_token or os.getenv("MIRO_ACCESS_TOKEN")
    if not token:
        raise ValueError("MIRO_ACCESS_TOKEN required")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    connectors: list[MiroConnector] = []
    cursor = None

    while True:
        params = {"limit": 50}
        if cursor:
            params["cursor"] = cursor

        response = requests.get(
            f"https://api.miro.com/v2/boards/{board_id}/connectors",
            headers=headers,
            params=params,
        )
        response.raise_for_status()
        data = response.json()

        for item in data.get("data", []):
            start_item = item.get("startItem", {})
            end_item = item.get("endItem", {})

            connectors.append(
                MiroConnector(
                    connector_id=str(item.get("id", "")),
                    start_item_id=str(start_item.get("id")) if start_item.get("id") else None,
                    end_item_id=str(end_item.get("id")) if end_item.get("id") else None,
                    stroke_style=item.get("style", {}).get("strokeStyle"),
                )
            )

        cursor = data.get("cursor")
        if not cursor:
            break

    return connectors


def determine_direction(start_x: float, end_x: float) -> str:
    """Determine edge direction based on X position.

    Board layout: RC ← SYM ← SC (right to left)
    So right direction (end_x > start_x) = forward (triggers/threatens/leads_to)

    Args:
        start_x: X position of start node
        end_x: X position of end node

    Returns:
        "forward" or "backward"
    """
    if end_x > start_x:
        return "forward"
    else:
        return "backward"


@dataclass
class EdgeResult:
    """Result of edge type determination."""

    edge_type: str
    from_miro_id: str  # Normalized: cause node
    to_miro_id: str    # Normalized: effect node
    swapped: bool      # True if original direction was reversed


def determine_edge_info(
    start_miro_id: str,
    end_miro_id: str,
    start_type: str,
    end_type: str,
    start_x: float,
    end_x: float,
) -> EdgeResult | None:
    """Determine edge type and normalized direction.

    For different node types, the edge direction is normalized based on
    the natural causal relationship (RC→SYM, SYM→SC), regardless of
    how the connector was drawn in Miro.

    Args:
        start_miro_id: Miro ID of connector start item
        end_miro_id: Miro ID of connector end item
        start_type: Node type of start item
        end_type: Node type of end item
        start_x: X position of start item
        end_x: X position of end item

    Returns:
        EdgeResult with normalized edge info, or None if unknown combination
    """
    # For different types, normalize to natural direction
    if start_type != end_type:
        # Define natural causal direction: cause → effect
        # RC → SYM (triggers), SYM → SC (threatens)
        NATURAL_CAUSE_EFFECT = {
            ("root_cause", "symptom"): ("triggers", False),
            ("symptom", "root_cause"): ("triggers", True),  # Swap needed
            ("symptom", "success_criteria"): ("threatens", False),
            ("success_criteria", "symptom"): ("threatens", True),  # Swap needed
        }

        if (start_type, end_type) in NATURAL_CAUSE_EFFECT:
            edge_type, swap = NATURAL_CAUSE_EFFECT[(start_type, end_type)]
            if swap:
                return EdgeResult(
                    edge_type=edge_type,
                    from_miro_id=end_miro_id,  # Swapped
                    to_miro_id=start_miro_id,  # Swapped
                    swapped=True,
                )
            else:
                return EdgeResult(
                    edge_type=edge_type,
                    from_miro_id=start_miro_id,
                    to_miro_id=end_miro_id,
                    swapped=False,
                )

        # Unknown cross-type combination
        return None

    # For same types, use position-based direction
    direction = determine_direction(start_x, end_x)
    edge_type = EDGE_TYPE_MAP.get((start_type, end_type, direction))

    if edge_type:
        return EdgeResult(
            edge_type=edge_type,
            from_miro_id=start_miro_id,
            to_miro_id=end_miro_id,
            swapped=False,
        )

    return None


def process_connectors(
    connectors: list[MiroConnector],
    miro_id_to_node: dict[str, dict],
) -> tuple[list[Edge], list[EdgeWarning]]:
    """Process connectors into edges with warnings.

    Args:
        connectors: List of MiroConnector objects
        miro_id_to_node: Mapping from miro_id to node data
            (must include 'node_type', 'position_x')

    Returns:
        Tuple of (edges, warnings)
    """
    edges: list[Edge] = []
    warnings: list[EdgeWarning] = []

    for conn in connectors:
        # Check for disconnected connectors
        if not conn.start_item_id or not conn.end_item_id:
            warnings.append(
                EdgeWarning(
                    connector_id=conn.connector_id,
                    warning_type="disconnected",
                    details={
                        "start_connected": conn.start_item_id is not None,
                        "end_connected": conn.end_item_id is not None,
                        "reason": (
                            "Both ends disconnected"
                            if not conn.start_item_id and not conn.end_item_id
                            else "Start not connected"
                            if not conn.start_item_id
                            else "End not connected"
                        ),
                    },
                )
            )
            continue

        # Look up node info
        start_node = miro_id_to_node.get(conn.start_item_id)
        end_node = miro_id_to_node.get(conn.end_item_id)

        # Skip if either node is not in our mapping (e.g., gray notes)
        if not start_node or not end_node:
            continue

        # Determine edge info with normalized direction
        edge_result = determine_edge_info(
            start_miro_id=conn.start_item_id,
            end_miro_id=conn.end_item_id,
            start_type=start_node["node_type"],
            end_type=end_node["node_type"],
            start_x=start_node["position_x"],
            end_x=end_node["position_x"],
        )

        if not edge_result:
            warnings.append(
                EdgeWarning(
                    connector_id=conn.connector_id,
                    warning_type="unknown_edge_type",
                    details={
                        "start_type": start_node["node_type"],
                        "end_type": end_node["node_type"],
                        "reason": f"Unexpected combination {start_node['node_type']}→{end_node['node_type']}",
                    },
                )
            )
            continue

        edges.append(
            Edge(
                from_miro_id=edge_result.from_miro_id,
                to_miro_id=edge_result.to_miro_id,
                edge_type=edge_result.edge_type,
                connector_id=conn.connector_id,
            )
        )

    return edges, warnings

