from abc import ABC
from typing import Dict, List
import random
from .Topology import Topology

class ScaleFreeTopology(Topology):
    """
    Barabási–Albert scale-free network topology.

    Parameters:
    - size: total number of nodes in the final graph
    - m0: number of nodes in the initial complete graph
    - m: number of edges each new node attaches with (m <= m0)
    - create_object_method: optional mapper from integer index to object
    """
    def __init__(self, size: int, m0: int, m: int, create_object_method=None):
        super().__init__(size, create_object_method)
        if m > m0:
            raise ValueError("m_parameter must be <= m0 (initial clique size)")
        if m0 < 1 or size < m0:
            raise ValueError("Require 1 <= m0 <= size")
        self.m0 = m0
        self.m = m

    def create(self) -> Dict[int, List]:
        # Initialize adjacency sets
        self._adj = [set() for _ in range(self.size)]

        # 1) Start with a complete graph on m0 nodes
        for u in range(self.m0):
            for v in range(u + 1, self.m0):
                self._adj[u].add(v)
                self._adj[v].add(u)

        # 2) Attach each new node i = m0 .. size-1
        for i in range(self.m0, self.size):
            # Compute degree-based attachment probabilities on existing nodes
            existing = list(range(i))
            degrees = [len(self._adj[j]) for j in existing]
            total_degree = sum(degrees)

            # Select m distinct targets using weighted sampling without replacement
            targets = set()
            while len(targets) < self.m:
                r = random.random() * total_degree
                cum = 0.0
                for j, deg in zip(existing, degrees):
                    cum += deg
                    if r < cum:
                        targets.add(j)
                        break

            # Add edges between new node and selected targets
            for j in targets:
                self._adj[i].add(j)
                self._adj[j].add(i)

        # Convert to output format with create_object_method
        return {
            
            i: [self.create_object_method(j) for j in sorted(self._adj[i])]
            for i in range(self.size)
        }