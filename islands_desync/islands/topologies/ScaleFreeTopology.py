from abc import ABC
from typing import Dict, List, Optional
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
    def __init__(self, size: int, m0: int, m: int, create_object_method=None, seed: Optional[int] = None):
        super().__init__(size, create_object_method)
        
        # Parameters validation
        if m0 < 2:
            raise ValueError("m0 must be at least 2 so that the initial graph has edges.")
        if size < m0:
            raise ValueError("size must be greater than or equal to m0.")
        if m < 1:
            raise ValueError("m must be at least 1.")
        if m > m0:
            raise ValueError("m must be less than or equal to m0.")
        
        self.m0 = m0
        self.m = m
        self._rng = random.Random(seed)

    def create(self) -> Dict[int, List]:
        # Initialize adjacency sets
        self._adj = [set() for _ in range(self.size)]
        rng = self._rng

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
                r = rng.random() * total_degree
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