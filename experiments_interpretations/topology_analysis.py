import json
import os
from datetime import datetime

import networkx as nx


def save_topology_analysis_from_adj(adj, params, output_dir=None, filename_prefix="topology"):
    """
    adj: List[set[int]] albo List[list[int]]
         np. topology_obj._adj z MeetingTopology

    params: obiekt z parametrami eksperymentu

    output_dir: katalog zapisu; jeśli None, bierze params.output_dir albo tworzy ./results
    """

    if output_dir is None:
        output_dir = getattr(params, "output_dir", "results")

    os.makedirs(output_dir, exist_ok=True)

    G = nx.Graph()

    # Dodaj wszystkie węzły, także izolowane
    G.add_nodes_from(range(len(adj)))

    # Dodaj krawędzie
    for u, neighbors in enumerate(adj):
        for v in neighbors:
            G.add_edge(u, v)

    n = G.number_of_nodes()
    m = G.number_of_edges()

    degrees = dict(G.degree())
    degree_values = list(degrees.values())

    components = list(nx.connected_components(G))
    component_sizes = [len(c) for c in components]

    largest_component_size = max(component_sizes) if component_sizes else 0

    metrics = {
        "timestamp": datetime.now().isoformat(),
        "nodes": n,
        "edges": m,
        "density": nx.density(G),
        "avg_degree": sum(degree_values) / n if n > 0 else 0,
        "min_degree": min(degree_values) if degree_values else 0,
        "max_degree": max(degree_values) if degree_values else 0,
        "avg_clustering": nx.average_clustering(G) if n > 0 else 0,
        "connected": nx.is_connected(G) if n > 0 else False,
        "components": nx.number_connected_components(G) if n > 0 else 0,
        "largest_component_size": largest_component_size,
    }

    # Ścieżki tylko jeśli graf spójny
    if n > 0 and nx.is_connected(G):
        metrics["avg_shortest_path_length"] = nx.average_shortest_path_length(G)
        metrics["diameter"] = nx.diameter(G)
    else:
        metrics["avg_shortest_path_length"] = None
        metrics["diameter"] = None

    # Modularność — przez greedy communities
    if m > 0:
        communities = list(nx.community.greedy_modularity_communities(G))
        metrics["community_count"] = len(communities)
        metrics["modularity"] = nx.community.modularity(G, communities)
        metrics["community_sizes"] = sorted([len(c) for c in communities], reverse=True)
    else:
        metrics["community_count"] = 0
        metrics["modularity"] = None
        metrics["community_sizes"] = []

    # Opcjonalnie: zapisz ważne parametry eksperymentu
    metrics["params"] = {
        "island_count": getattr(params, "island_count", None),
        "topology": getattr(params, "topology", None),
        "seed": getattr(params, "seed", None),
        "m0": getattr(params, "m0", None),
        "m": getattr(params, "m", None),
        "z_star": getattr(params, "z_star", None),
        "n_steps": getattr(params, "n_steps", None),
        "npr0": getattr(params, "npr0", None),
        "nmr1": getattr(params, "nmr1", None),
        "ne_gamma": getattr(params, "ne_gamma", None),
    }

    print("Saving topology to:", os.path.abspath(output_dir))
    metrics_path = os.path.join(output_dir, f"{filename_prefix}_metrics.json")
    edgelist_path = os.path.join(output_dir, f"{filename_prefix}.edgelist")
    graphml_path = os.path.join(output_dir, f"{filename_prefix}.graphml")

    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

    nx.write_edgelist(G, edgelist_path, data=False)
    nx.write_graphml(G, graphml_path)

    return metrics