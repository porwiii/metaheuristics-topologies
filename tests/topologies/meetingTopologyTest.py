import networkx as nx
import matplotlib.pyplot as plt
from collections import Counter
from MeetingTopology import MeetingTopology


def dict_adj_to_nx(graph_dict):
    """
    graph_dict: Dict[int, List[int]] (lista sąsiadów)
    Zwraca prosty graf nieskierowany.
    """
    G = nx.Graph()
    G.add_nodes_from(graph_dict.keys())
    for u, neighs in graph_dict.items():
        for v in neighs:
            if u != v:
                G.add_edge(u, v)
    return G

def basic_stats(G: nx.Graph):
    n = G.number_of_nodes()
    m = G.number_of_edges()
    degs = [d for _, d in G.degree()]
    cc = nx.average_clustering(G)


    # spójność / średnia długość ścieżek tylko dla największej składowej
    if n > 0:
        components = list(nx.connected_components(G))
        gcc = max(components, key=len)
        G_gcc = G.subgraph(gcc).copy()
        gcc_size = G_gcc.number_of_nodes()
        C_trans_gcc = nx.transitivity(G_gcc)
    else:
        G_gcc = G
        gcc_size = 0

    out = {
        "n_nodes": n,
        "n_edges": m,
        "density": nx.density(G) if n > 1 else 0.0,
        "avg_degree": (2*m/n) if n > 0 else 0.0,
        "min_degree": min(degs) if degs else 0,
        "max_degree": max(degs) if degs else 0,
        "avg_clustering": cc,
        "n_components": nx.number_connected_components(G) if n > 0 else 0,
        "gcc_size": gcc_size,
        "transivity": C_trans_gcc,
    }

    if gcc_size >= 2:
        out["avg_shortest_path_len_gcc"] = nx.average_shortest_path_length(G_gcc)
        out["diameter_gcc"] = nx.diameter(G_gcc)
    else:
        out["avg_shortest_path_len_gcc"] = None
        out["diameter_gcc"] = None

    # assortativity by degree (czy "bogaci łączą się z bogatymi")
    try:
        out["degree_assortativity"] = nx.degree_assortativity_coefficient(G)
    except Exception:
        out["degree_assortativity"] = None

    return out

def detect_communities(G: nx.Graph):
    """
    Zwraca: (communities, modularity)
    communities: lista zbiorów wierzchołków
    """
    # wbudowany algorytm: greedy modularity (działa bez dodatkowych paczek)
    from networkx.algorithms.community import greedy_modularity_communities, modularity

    comms = list(greedy_modularity_communities(G))
    Q = modularity(G, comms) if comms else None
    return comms, Q

def print_community_summary(comms):
    sizes = sorted([len(c) for c in comms], reverse=True)
    print("Liczba communities:", len(comms))
    print("Rozmiary (top 10):", sizes[:10])
    print("Rozkład rozmiarów:", dict(Counter(sizes)))

def visualize_communities(G: nx.Graph, comms, title="Community structure", seed=42):
    """
    Prosta wizualizacja: spring_layout + kolory per community.
    """
    # map: node -> community_id
    node2c = {}
    for cid, cset in enumerate(comms):
        for node in cset:
            node2c[node] = cid

    # kolor jako liczba całkowita (matplotlib sam dobierze paletę)
    colors = [node2c.get(n, -1) for n in G.nodes()]

    pos = nx.spring_layout(G, seed=seed)  # dla 200 węzłów ok; dla większych może być wolne
    plt.figure(figsize=(10, 8))
    nx.draw_networkx_nodes(G, pos, node_size=40, node_color=colors)
    nx.draw_networkx_edges(G, pos, alpha=0.15, width=0.7)
    plt.title(title)
    plt.axis("off")
    plt.show()

n=250

top = MeetingTopology(
    size=n,
    z_star=5,
    n_steps=500,
    npr0=int(n**2*0.0005),
    nmr1=4850,
    ne_gamma=int(n*0.005),
    gamma=1.0,
    seed=123,
)

# top = MeetingTopology(
#     size=30,
#     z_star=10,
#     n_steps=500,
#     npr0=50,
#     nmr1=30,
#     ne_gamma=10,
#     gamma=1.0,
#     seed=123,
# )
graph = top.generate_topology()
# --- użycie na Twoim grafie ---
G = dict_adj_to_nx(graph)

stats = basic_stats(G)
print("== Basic stats ==")
for k, v in stats.items():
    print(f"{k}: {v}")

comms, Q = detect_communities(G)
print("\n== Communities ==")
print_community_summary(comms)
print("Modularity Q:", Q)

visualize_communities(G, comms, title=f"Community structure (Q={Q:.3f})" if Q is not None else "Community structure")
