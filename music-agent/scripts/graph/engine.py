#!/usr/bin/env python3
"""
engine.py - NetworkX-based graph traversal engine for the music-agent knowledge graph.

Usage:
    python3 scripts/graph/engine.py shortest-path <source_id> <target_id>
    python3 scripts/graph/engine.py ego <entity_id> [depth]
    python3 scripts/graph/engine.py border <id1,id2,...|auto>
    python3 scripts/graph/engine.py walk <start_id> [steps]
    python3 scripts/graph/engine.py centrality [top_n]
    python3 scripts/graph/engine.py clusters [min_size]
    python3 scripts/graph/engine.py stats
"""

import json
import random
import sqlite3
import sys
from collections import Counter
from pathlib import Path

import networkx as nx

DB_PATH = Path.home() / ".music-agent" / "knowledge.db"


# ---------------------------------------------------------------------------
# Core graph functions
# ---------------------------------------------------------------------------

def load_graph(conn=None):
    """Load the knowledge graph from SQLite into a networkx Graph.

    Args:
        conn: An existing sqlite3.Connection, or None to connect to the default DB.

    Returns:
        A networkx.Graph with entity nodes and relation edges.
    """
    close_conn = False
    if conn is None:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        close_conn = True

    G = nx.Graph()

    # Determine available columns (discogs_id may not exist yet)
    cursor = conn.execute("PRAGMA table_info(entities)")
    columns = {row[1] for row in cursor.fetchall()}
    has_discogs = "discogs_id" in columns

    if has_discogs:
        entity_sql = "SELECT id, type, name, metadata, sources, apple_music_id, discogs_id FROM entities"
    else:
        entity_sql = "SELECT id, type, name, metadata, sources, apple_music_id FROM entities"

    for row in conn.execute(entity_sql):
        attrs = {
            "type": row[1],
            "name": row[2],
            "metadata": row[3],
            "sources": row[4],
            "apple_music_id": row[5],
        }
        if has_discogs:
            attrs["discogs_id"] = row[6]
        G.add_node(row[0], **attrs)

    for row in conn.execute(
        "SELECT source_id, target_id, relation, confidence, metadata FROM relations"
    ):
        G.add_edge(row[0], row[1], relation=row[2], confidence=row[3], metadata=row[4])

    if close_conn:
        conn.close()

    return G


def shortest_path(G, source, target):
    """Find the shortest path between two nodes.

    Returns:
        List of node IDs from source to target, or None if no path exists.
    """
    try:
        return nx.shortest_path(G, source, target)
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return None


def path_detail(G, path):
    """Return detailed info for each node in a path, including connecting edge relations.

    Args:
        G: The graph.
        path: List of node IDs.

    Returns:
        List of dicts. Each dict has node info (id, name, type) and, for nodes
        after the first, an edge_relation field describing how they connect to
        the previous node.
    """
    details = []
    for i, node_id in enumerate(path):
        info = {"id": node_id}
        node_data = G.nodes.get(node_id, {})
        info["name"] = node_data.get("name", node_id)
        info["type"] = node_data.get("type", "unknown")
        if i > 0:
            edge_data = G.edges.get((path[i - 1], node_id), {})
            info["edge_relation"] = edge_data.get("relation", "connected")
        details.append(info)
    return details


def ego_graph(G, entity_id, depth=1):
    """Return the ego graph (subgraph of neighbors) around an entity.

    Args:
        G: The graph.
        entity_id: Center node.
        depth: Radius of the ego graph.

    Returns:
        A networkx subgraph.
    """
    return nx.ego_graph(G, entity_id, radius=depth)


def border_nodes(G, collection_ids):
    """Find nodes just outside a collection that connect to it.

    Args:
        G: The graph.
        collection_ids: Set of node IDs representing the collection.

    Returns:
        List of (node_id, connection_count) tuples, sorted by count descending.
    """
    neighbor_counts = Counter()
    for node_id in collection_ids:
        for neighbor in G.neighbors(node_id):
            if neighbor not in collection_ids:
                neighbor_counts[neighbor] += 1
    return sorted(neighbor_counts.items(), key=lambda x: -x[1])


def random_walk(G, start, steps=5, edge_types=None):
    """Perform a random walk on the graph, avoiding revisits when possible.

    Args:
        G: The graph.
        start: Starting node ID.
        steps: Maximum number of steps.
        edge_types: Optional list of edge relation types to follow.

    Returns:
        List of node IDs visited.
    """
    walk = [start]
    current = start
    for _ in range(steps):
        neighbors = list(G.neighbors(current))
        if edge_types:
            neighbors = [
                n for n in neighbors
                if G.edges[current, n].get("relation") in edge_types
            ]
        if not neighbors:
            break
        # Prefer unvisited neighbors
        unvisited = [n for n in neighbors if n not in walk]
        if unvisited:
            current = random.choice(unvisited)
        else:
            current = random.choice(neighbors)
        walk.append(current)
    return walk


def centrality(G, top_n=None):
    """Compute betweenness centrality for all nodes.

    Args:
        G: The graph.
        top_n: If set, return only the top N nodes.

    Returns:
        Dict of {node_id: centrality_score}.
    """
    scores = nx.betweenness_centrality(G)
    if top_n is not None:
        top_items = sorted(scores.items(), key=lambda x: -x[1])[:top_n]
        return dict(top_items)
    return scores


def clusters(G, min_size=1):
    """Find communities using greedy modularity optimization.

    Args:
        G: The graph.
        min_size: Minimum community size to include.

    Returns:
        List of sets of node IDs.
    """
    if G.number_of_nodes() == 0:
        return []
    communities = list(nx.community.greedy_modularity_communities(G))
    return [c for c in communities if len(c) >= min_size]


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def _enrich_node(G, node_id):
    """Return a dict with id, name, type for a node."""
    data = G.nodes.get(node_id, {})
    return {
        "id": node_id,
        "name": data.get("name", node_id),
        "type": data.get("type", "unknown"),
    }


def cli_shortest_path(args):
    if len(args) < 2:
        return {"error": "Usage: shortest-path <source_id> <target_id>"}
    G = load_graph()
    path = shortest_path(G, args[0], args[1])
    if path is None:
        return {"path": None, "message": "No path found"}
    return {"path": path, "detail": path_detail(G, path), "length": len(path) - 1}


def cli_ego(args):
    if len(args) < 1:
        return {"error": "Usage: ego <entity_id> [depth]"}
    entity_id = args[0]
    depth = int(args[1]) if len(args) > 1 else 1
    G = load_graph()
    sub = ego_graph(G, entity_id, depth=depth)
    nodes = [_enrich_node(sub, n) for n in sub.nodes]
    edges = [
        {"source": u, "target": v, "relation": d.get("relation", "connected")}
        for u, v, d in sub.edges(data=True)
    ]
    return {"center": entity_id, "depth": depth, "nodes": nodes, "edges": edges}


def cli_border(args):
    if len(args) < 1:
        return {"error": "Usage: border <id1,id2,...|auto>"}
    G = load_graph()
    if args[0] == "auto":
        collection_ids = {
            n for n, d in G.nodes(data=True) if d.get("apple_music_id")
        }
    else:
        collection_ids = set(args[0].split(","))
    borders = border_nodes(G, collection_ids)
    return {
        "collection_size": len(collection_ids),
        "border_nodes": [_enrich_node(G, nid) | {"connections": cnt} for nid, cnt in borders],
    }


def cli_walk(args):
    if len(args) < 1:
        return {"error": "Usage: walk <start_id> [steps]"}
    start = args[0]
    steps = int(args[1]) if len(args) > 1 else 5
    G = load_graph()
    walk = random_walk(G, start, steps=steps)
    return {"walk": [_enrich_node(G, n) for n in walk], "length": len(walk)}


def cli_centrality(args):
    top_n = int(args[0]) if args else None
    G = load_graph()
    scores = centrality(G, top_n=top_n)
    ranked = sorted(scores.items(), key=lambda x: -x[1])
    return {
        "nodes": [_enrich_node(G, nid) | {"score": round(s, 6)} for nid, s in ranked],
    }


def cli_clusters(args):
    min_size = int(args[0]) if args else 1
    G = load_graph()
    comms = clusters(G, min_size=min_size)
    return {
        "count": len(comms),
        "clusters": [
            {"size": len(c), "members": [_enrich_node(G, n) for n in c]}
            for c in comms
        ],
    }


def cli_stats(_args):
    G = load_graph()
    type_counts = Counter()
    for _, d in G.nodes(data=True):
        type_counts[d.get("type", "unknown")] += 1
    return {
        "nodes": G.number_of_nodes(),
        "edges": G.number_of_edges(),
        "density": round(nx.density(G), 6),
        "components": nx.number_connected_components(G),
        "nodeTypes": dict(type_counts),
    }


# ---------------------------------------------------------------------------
# CLI dispatch
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: engine.py <command> [args]"}))
        sys.exit(1)

    cmd = sys.argv[1]
    cmd_args = sys.argv[2:]

    dispatch = {
        "shortest-path": cli_shortest_path,
        "ego": cli_ego,
        "border": cli_border,
        "walk": cli_walk,
        "centrality": cli_centrality,
        "clusters": cli_clusters,
        "stats": cli_stats,
    }

    fn = dispatch.get(cmd)
    if not fn:
        print(json.dumps({"error": f"Unknown command: {cmd}"}))
        sys.exit(1)

    try:
        print(json.dumps(fn(cmd_args), indent=2, default=str))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)
