from typing import Dict, List, Callable, Optional
import random
from .Topology import Topology


class MeetingTopology(Topology):
    """
    Implementation of Model II from the paper "The Structure of Growing Social Networks".

    The model assumes:
    1) a fixed number of vertices,
    2) a hard degree cap z_star,
    3) edge creation through random meetings,
    4) edge creation through mutual acquaintances,
    5) random decay of existing edges.

    Parameters:
    - size: number of vertices N
    - z_star: maximum vertex degree
    - n_steps: number of steps in the dynamic phase
    - r0: base rate of random pairwise meetings
    - r1: rate of meetings through mutual acquaintances
    - gamma: decay rate of existing edges
    - build_target_ratio: threshold for the build phase, e.g. 0.8 means an average degree of 0.8 * z_star
    - max_build_steps: safeguard against an infinite build phase
    - create_object_method: mapping from index -> object
    - seed: optional RNG seed
    """

    def __init__(
        self,
        size: int,
        z_star: int,
        n_steps: int,
        r0: float,
        r1: float,
        gamma: float,
        build_target_ratio: float = 0.8,
        max_build_steps: Optional[int] = None,
        create_object_method: Optional[Callable[[int], object]] = None,
        seed: Optional[int] = None,
    ):
        super().__init__(size, create_object_method)

        self.size = size
        self.z_star = z_star
        self.n_steps = n_steps

        self.r0 = r0
        self.r1 = r1
        self.gamma = gamma

        self.build_target_ratio = build_target_ratio
        self.max_build_steps = max_build_steps
        self._rng = random.Random(seed)

    def create(self) -> Dict[int, List[object]]:
        """
        Builds the topology according to Model II:

        phase 1:
            step1
            step2

        phase 2:
            step1
            step2
            step3
        """

        # adjacency list as sets — fast edge-existence lookups
        self._adj: List[set[int]] = [set() for _ in range(self.size)]

        # phase 1: build network
        self._phase1_build_network()

        # phase 2: dynamic equilibrium
        for _ in range(self.n_steps):
            self._step1_random_meetings()
            self._step2_neighbor_meetings()
            self._step3_edge_deletions()

        # safeguard for leftover isolated islands - connect each to one random island
        self._connect_isolated_nodes()

        return {
            i: [self.create_object_method(j) for j in sorted(self._adj[i])]
            for i in range(self.size)
        }

    # Main phases
    def _phase1_build_network(self):
        """
        Phase 1: build the network.

        We start from an empty graph. We only run steps 1 and 2,
        without edge removal, until the average degree reaches
        build_target_ratio * z_star.

        The paper describes this as running the first two steps
        until all or most vertices reach degree z_star. Here we use
        a practical average-degree threshold instead.
        """
        target_avg_degree = self.build_target_ratio * self.z_star

        if self.max_build_steps is None:
            max_steps = max(1000, 10 * self.size * max(1, self.z_star))
        else:
            max_steps = self.max_build_steps

        steps = 0
        stagnant_steps = 0

        while self._avg_degree() < target_avg_degree and steps < max_steps:
            before_edges = self._edge_count()

            self._step1_random_meetings()
            self._step2_neighbor_meetings()

            after_edges = self._edge_count()

            if after_edges == before_edges:
                stagnant_steps += 1
            else:
                stagnant_steps = 0

            # safeguard: if nothing changes for many steps in a row,
            # further building is unlikely to help
            if stagnant_steps >= 100:
                break

            steps += 1

    def _connect_isolated_nodes(self) -> None:
        for i in range(self.size):
            if self._deg(i) != 0:
                continue

            other_nodes = [j for j in range(self.size) if j != i]
            candidates_below_limit = [j for j in other_nodes if self._can_add_more(j)]

            j = self._rng.choice(candidates_below_limit or other_nodes)

            self._adj[i].add(j)
            self._adj[j].add(i)

    # Model steps
    def _step1_random_meetings(self):
        """
        1) Random pairwise meetings.

        In each step we pick np * r0 vertex pairs uniformly at random.
        If the pair has no edge yet and both vertices have degree < z_star,
        we add an edge.
        """
        k = self._event_count(self._num_pairs() * self.r0)

        for _ in range(k):
            u, v = self._rng.sample(range(self.size), 2)
            self._try_add_edge(u, v)

    def _step2_neighbor_meetings(self):
        """
        2) Meetings through mutual acquaintances.

        We pick nm * r1 vertices with probability proportional to
        z_i * (z_i - 1). Then, for each chosen vertex, we pick a random
        pair of its neighbors and try to add an edge between them.
        """
        weights = [
            float(self._deg(i) * (self._deg(i) - 1))
            for i in range(self.size)
        ]

        nm = self._num_mutual_opportunities()
        k = self._event_count(nm * self.r1)

        chosen_vertices = self._weighted_choices(weights, k)

        for i in chosen_vertices:
            neighbors = list(self._adj[i])

            if len(neighbors) < 2:
                continue

            a, b = self._rng.sample(neighbors, 2)
            self._try_add_edge(a, b)

    def _step3_edge_deletions(self):
        """
        3) Edge decay.

        We pick ne * gamma vertices with probability proportional to z_i.
        Then, for each chosen vertex, we remove the edge to a random
        neighbor.
        """
        weights = [
            float(self._deg(i))
            for i in range(self.size)
        ]

        ne = self._edge_count()
        k = self._event_count(ne * self.gamma)

        chosen_vertices = self._weighted_choices(weights, k)

        for i in chosen_vertices:
            if not self._adj[i]:
                continue

            j = self._rng.choice(tuple(self._adj[i]))
            self._try_remove_edge(i, j)

    # Graph modification helpers
    def _can_add_more(self, i: int) -> bool:
        return self._deg(i) < self.z_star

    def _try_add_edge(self, u: int, v: int) -> bool:
        if u == v:
            return False

        if not (0 <= u < self.size and 0 <= v < self.size):
            return False

        if v in self._adj[u]:
            return False

        if not (self._can_add_more(u) and self._can_add_more(v)):
            return False

        self._adj[u].add(v)
        self._adj[v].add(u)
        return True

    def _try_remove_edge(self, u: int, v: int) -> bool:
        if not (0 <= u < self.size and 0 <= v < self.size):
            return False

        if v not in self._adj[u]:
            return False

        self._adj[u].remove(v)
        self._adj[v].remove(u)
        return True

    # Graph metrics
    def _deg(self, i: int) -> int:
        return len(self._adj[i])

    def _num_pairs(self) -> int:
        """
        np = 1/2 * N * (N - 1)
        Number of all possible vertex pairs.
        """
        return self.size * (self.size - 1) // 2

    def _edge_count(self) -> int:
        """
        ne = number of existing edges.
        """
        return sum(len(neighbors) for neighbors in self._adj) // 2

    def _avg_degree(self) -> float:
        if self.size == 0:
            return 0.0

        return 2.0 * self._edge_count() / self.size

    def _num_mutual_opportunities(self) -> float:
        """
        nm = 1/2 * sum_i z_i * (z_i - 1)

        The paper defines this as the total number of "opportunities"
        for meetings through a mutual acquaintance.
        """
        return 0.5 * sum(
            self._deg(i) * (self._deg(i) - 1)
            for i in range(self.size)
        )

    # Randomness helpers
    def _event_count(self, expected_value: float) -> int:
        """
        Converts an expected event count into an integer count.

        Example:
        - 15.2 usually gives 15, occasionally 16,
        - 0.05 gives one event with probability 0.05.

        This way we don't lose small frequencies such as ne * gamma < 1.
        """
        if expected_value <= 0:
            return 0

        base = int(expected_value)
        fraction = expected_value - base

        if self._rng.random() < fraction:
            return base + 1

        return base

    def _weighted_choices(self, weights: List[float], k: int) -> List[int]:
        """
        Sampling with replacement.

        If the total weight is 0, returns an empty list.
        """
        total = sum(weights)

        if total <= 0 or k <= 0:
            return []

        population = list(range(self.size))
        return self._rng.choices(population, weights=weights, k=k)
