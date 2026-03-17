"""Tests for the graph engine traversal primitives."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "graph"))


def test_load_graph(populated_db):
    from engine import load_graph
    G = load_graph(populated_db)
    assert G.number_of_nodes() == 10
    assert G.number_of_edges() == 13


def test_shortest_path(populated_db):
    from engine import load_graph, shortest_path
    G = load_graph(populated_db)
    path = shortest_path(G, "mbid-artist-1", "mbid-artist-3")
    assert path is not None
    assert path[0] == "mbid-artist-1"
    assert path[-1] == "mbid-artist-3"
    assert len(path) >= 3


def test_shortest_path_no_connection(populated_db):
    from engine import load_graph, shortest_path
    G = load_graph(populated_db)
    G.add_node("island", type="artist", name="Isolated Artist")
    path = shortest_path(G, "mbid-artist-1", "island")
    assert path is None


def test_ego_graph(populated_db):
    from engine import load_graph, ego_graph
    G = load_graph(populated_db)
    subgraph = ego_graph(G, "mbid-engineer-1", depth=1)
    assert "mbid-engineer-1" in subgraph.nodes
    assert subgraph.number_of_nodes() >= 4


def test_border_nodes(populated_db):
    from engine import load_graph, border_nodes
    G = load_graph(populated_db)
    collection_ids = {"mbid-release-1", "mbid-release-3"}
    borders = border_nodes(G, collection_ids)
    assert len(borders) > 0
    for node_id, _ in borders:
        assert node_id not in collection_ids


def test_random_walk(populated_db):
    from engine import load_graph, random_walk
    G = load_graph(populated_db)
    walk = random_walk(G, "mbid-artist-1", steps=4)
    assert walk[0] == "mbid-artist-1"
    assert len(walk) <= 5
    for i in range(1, len(walk)):
        assert G.has_edge(walk[i - 1], walk[i]) or G.has_edge(walk[i], walk[i - 1])


def test_centrality(populated_db):
    from engine import load_graph, centrality
    G = load_graph(populated_db)
    scores = centrality(G)
    top_ids = [node_id for node_id, _ in sorted(scores.items(), key=lambda x: -x[1])[:3]]
    assert "mbid-label-1" in top_ids


def test_clusters(populated_db):
    from engine import load_graph, clusters
    G = load_graph(populated_db)
    communities = clusters(G)
    assert len(communities) >= 1
    all_nodes = set()
    for c in communities:
        all_nodes.update(c)
    assert all_nodes == set(G.nodes)


def test_path_detail(populated_db):
    from engine import load_graph, path_detail
    G = load_graph(populated_db)
    path = ["mbid-artist-1", "mbid-release-1", "mbid-engineer-1"]
    detail = path_detail(G, path)
    assert len(detail) == 3
    assert detail[0]["name"] == "Autechre"
    assert detail[0]["type"] == "artist"
    assert "edge_relation" in detail[1]
