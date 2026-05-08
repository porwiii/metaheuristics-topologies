from typing import Dict, List, Callable, Optional
import random
from abc import ABC


class Topology(ABC):
    def __init__(self, size, create_object_method=None):
        self.size = size
        self.create_object_method = (
            (lambda i: int(i)) if create_object_method is None else create_object_method
        )

    def create(self) -> Dict[int, List]:
        pass

class MeetingTopology(Topology):
    """
    Implementacja algorytmu z opisu:

    1) npr0 losowych par wierzchołków (jednostajnie): dodaj krawędź jeśli brak i oba < z_star
    2) nmr1 wierzchołków z wagą ~ z_i(z_i-1): wybierz losową parę sąsiadów i dodaj krawędź między nimi
    3) ne_gamma wierzchołków z wagą ~ z_i^gamma: usuń krawędź do losowego sąsiada

    Parametry:
    - size: liczba wierzchołków
    - z_star: maksymalny stopień (limit połączeń)
    - n_steps: liczba kroków czasowych (time-steps)
    - npr0, nmr1, ne_gamma: liczby zdarzeń na krok
    - gamma: wykładnik w kroku (3); ustaw 1 aby było ~ z_i
    - create_object_method: mapowanie indeksu -> obiekt (jak w Twoim przykładzie)
    - seed: opcjonalny seed RNG
    """
    def __init__(self, size: int, z_star: int, n_steps: int, npr0: int, nmr1: int, ne_gamma: int, gamma: float = 1.0,
                 create_object_method: Optional[Callable[[int], object]] = None, seed: Optional[int] = None,
                 initial_edges: Optional[List[tuple[int, int]]] = None):
        super().__init__(size, create_object_method)
        self.size = size
        self.z_star = z_star
        self.n_steps = n_steps
        self.npr0 = npr0
        self.nmr1 = nmr1
        self.ne_gamma = ne_gamma
        self.gamma = gamma
        self.create_object_method = create_object_method or (lambda x: x)

        if seed is not None:
            random.seed(seed)

        # adjacency list jako sety (szybkie sprawdzanie istnienia krawędzi)
        self._adj: List[set[int]] = [set() for _ in range(size)]

        # opcjonalna inicjalizacja grafu
        if initial_edges:
            for u, v in initial_edges:
                self._try_add_edge(u, v)

    def _deg(self, i: int) -> int:
        return len(self._adj[i])

    def _can_add_more(self, i: int) -> bool:
        return self._deg(i) < self.z_star

    def _try_add_edge(self, u: int, v: int) -> bool:
        if u == v:
            return False
        if v in self._adj[u]:
            return False
        if not (self._can_add_more(u) and self._can_add_more(v)):
            return False
        self._adj[u].add(v)
        self._adj[v].add(u)
        return True

    def _try_remove_edge(self, u: int, v: int) -> bool:
        if v not in self._adj[u]:
            return False
        self._adj[u].remove(v)
        self._adj[v].remove(u)
        return True

    def _weighted_choices(self, weights: List[float], k: int) -> List[int]:
        """
        Losowanie z powtórzeniami (jak w opisie: 'choose n ... vertices at random with probabilities ...').
        Jeśli suma wag = 0, zwraca pustą listę.
        """
        total = sum(weights)
        if total <= 0 or k <= 0:
            return []
        population = list(range(self.size))
        return random.choices(population, weights=weights, k=k)
    
    def _edge_count(self) -> int:
        return sum(len(neigh) for neigh in self._adj) // 2

    def _avg_degree(self) -> float:
        return 2 * self._edge_count() / self.size if self.size > 0 else 0.0

    def _step1_random_meetings(self):
        # 1) npr0 par losowych (uniform)
        for _ in range(self.npr0):
            u, v = random.sample(range(self.size), 2)
            self._try_add_edge(u, v)

    def _step2_neighbor_meetings(self):
        # 2) wybierz nmr1 wierzchołków z wagą ~ z_i(z_i-1)
        weights = []
        for i in range(self.size):
            z = self._deg(i)
            weights.append(float(z * (z - 1)))  # 0 dla z<2

        chosen_vertices = self._weighted_choices(weights, self.nmr1)

        for i in chosen_vertices:
            neighbors = list(self._adj[i])
            if len(neighbors) < 2:
                continue

            a, b = random.sample(neighbors, 2)  # losowa para sąsiadów
            self._try_add_edge(a, b)

    def _step3_edge_deletions(self):
        # 3) wybierz ne_gamma wierzchołków z wagą ~ z_i^gamma (dla gamma=1 -> ~ z_i)
        weights = []
        for i in range(self.size):
            z = self._deg(i)
            weights.append(float(z ** self.gamma) if z > 0 else 0.0)

        chosen_vertices = self._weighted_choices(weights, self.ne_gamma)

        for i in chosen_vertices:
            if not self._adj[i]:
                continue
            j = random.choice(tuple(self._adj[i]))  # losowy sąsiad
            self._try_remove_edge(i, j)

    def _phase1_build_network(self, target_ratio: float = 0.8, max_build_steps: Optional[int] = None):
        target_avg_degree = self.z_star * target_ratio

        if max_build_steps is None:
            # zabezpieczenie przed pętlą nieskończoną
            max_build_steps = max(1000, 10 * self.size * self.z_star)

        steps = 0

        while self._avg_degree() < target_avg_degree and steps < max_build_steps:
            before_edges = self._edge_count()

            self._step1_random_meetings()
            self._step2_neighbor_meetings()

            after_edges = self._edge_count()
            steps += 1

            # jeżeli przez dłuższy czas nic nie da się dodać, kończymy
            if after_edges == before_edges:
                break


    def create(self) -> Dict[int, List[object]]:
        # phase 1: build network
        self._phase1_build_network(target_ratio=0.8)

        # phase 2: dynamic equilibrium
        for _ in range(self.n_steps):
            self._step1_random_meetings()
            self._step2_neighbor_meetings()
            self._step3_edge_deletions()

        # zabezpieczenie kiedy zostają izolowane wyspy - łaczymy je z 1 losową wyspą
        for i in range(self.size):
            if len(self._adj[i]) == 0:
                candidates = [
                    j for j in range(self.size)
                    if j != i and len(self._adj[j]) < self.z_star
                ]

                if not candidates:
                    candidates = [j for j in range(self.size) if j != i]

                j = random.choice(candidates)
                self._adj[i].add(j)
                self._adj[j].add(i)

        return {
            i: [self.create_object_method(j) for j in sorted(self._adj[i])]
            for i in range(self.size)
        }

    ## TODO
    # # phase 1: build network
    # while avg_degree < z_star * 0.8:
    #     step1
    #     step2
    #
    # # phase 2: dynamic equilibrium
    # for t in steps:
    #     step1
    #     step2
    #     step3


# top = MeetingTopology(
#     size=250,
#     z_star=5,
#     n_steps=500,
#     npr0=int(250**2*0.0005),
#     nmr1=250*2,
#     ne_gamma=int(250*0.005),
#     gamma=1.0,
#     seed=123,
# )
# graph = top.generate_topology()
# print(graph[0])  # lista sąsiadów wierzchołka 0

