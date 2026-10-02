import unittest

import networkx as nx

from islands_desync.islands.topologies.CommunityTopology import CommunityTopology


def _graph_from_adjacency(adjacency: dict) -> nx.Graph:
    graph = nx.Graph()
    graph.add_nodes_from(adjacency.keys())
    for node, neighbors in adjacency.items():
        for neighbor in neighbors:
            graph.add_edge(node, neighbor)
    return graph


class CommunityTopologyTest(unittest.TestCase):
    def test_no_dynamic_phase_params(self):
        # CommunityTopology should not accept n_steps/gamma anymore.
        with self.assertRaises(TypeError):
            CommunityTopology(
                size=20,
                z_star=5,
                r0=0.05,
                r1=1.0,
                n_steps=10,
                gamma=0.1,
                seed=1,
            )

    def test_graph_is_always_fully_connected(self):
        for seed in range(10):
            adjacency = CommunityTopology(
                size=60,
                z_star=4,
                r0=0.01,
                r1=0.5,
                build_target_ratio=0.5,
                seed=seed,
            ).create()

            graph = _graph_from_adjacency(adjacency)

            self.assertTrue(
                nx.is_connected(graph),
                msg=f"graph not connected for seed={seed}",
            )
            self.assertEqual(nx.number_connected_components(graph), 1)

    def test_bridge_prefers_nodes_below_degree_cap(self):
        topology = CommunityTopology(
            size=6,
            z_star=2,
            r0=0.0,
            r1=0.0,
            build_target_ratio=0.0,
            seed=0,
        )
        topology._adj = [set() for _ in range(topology.size)]

        # two disconnected components: {0, 1, 2} and {3, 4, 5}
        topology._adj[0].add(1)
        topology._adj[1].add(0)
        topology._adj[1].add(2)
        topology._adj[2].add(1)

        topology._adj[3].add(4)
        topology._adj[4].add(3)
        topology._adj[4].add(5)
        topology._adj[5].add(4)

        # node 1 and node 4 are already at the z_star=2 cap
        topology._connect_components()

        graph = nx.Graph()
        graph.add_nodes_from(range(topology.size))
        for u, neighbors in enumerate(topology._adj):
            for v in neighbors:
                graph.add_edge(u, v)

        self.assertTrue(nx.is_connected(graph))
        # the bridge edge should avoid the saturated nodes 1 and 4
        bridge_edges = [(0, 3), (0, 5), (2, 3), (2, 5)]
        self.assertTrue(any(graph.has_edge(*edge) for edge in bridge_edges))


if __name__ == "__main__":
    unittest.main()
