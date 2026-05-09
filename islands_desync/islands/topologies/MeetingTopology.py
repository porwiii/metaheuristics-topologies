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
    Implementacja Modelu II z artykułu "The Structure of Growing Social Networks".

    Model zakłada:
    1) stałą liczbę wierzchołków,
    2) twardy limit stopnia z_star,
    3) tworzenie krawędzi przez losowe spotkania,
    4) tworzenie krawędzi przez wspólnych znajomych,
    5) losowe zanikanie istniejących krawędzi.

    Parametry:
    - size: liczba wierzchołków N
    - z_star: maksymalny stopień wierzchołka
    - n_steps: liczba kroków fazy dynamicznej
    - r0: bazowe tempo losowych spotkań par
    - r1: tempo spotkań przez wspólnych znajomych
    - gamma: tempo zaniku istniejących krawędzi
    - build_target_ratio: próg fazy budowania, np. 0.8 oznacza średni stopień 0.8 * z_star
    - max_build_steps: zabezpieczenie przed nieskończoną fazą budowania
    - create_object_method: mapowanie indeksu -> obiekt
    - seed: opcjonalny seed RNG
    - initial_edges: opcjonalna lista początkowych krawędzi
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
        initial_edges: Optional[List[tuple[int, int]]] = None,
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

        self.create_object_method = create_object_method or (lambda x: x)

        if seed is not None:
            random.seed(seed)

        # adjacency list jako sety — szybkie sprawdzanie istnienia krawędzi
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

    def _num_pairs(self) -> int:
        """
        np = 1/2 * N * (N - 1)
        Liczba wszystkich możliwych par wierzchołków.
        """
        return self.size * (self.size - 1) // 2

    def _edge_count(self) -> int:
        """
        ne = liczba istniejących krawędzi.
        """
        return sum(len(neighbors) for neighbors in self._adj) // 2

    def _avg_degree(self) -> float:
        if self.size == 0:
            return 0.0

        return 2.0 * self._edge_count() / self.size

    def _num_mutual_opportunities(self) -> float:
        """
        nm = 1/2 * sum_i z_i * (z_i - 1)

        W artykule jest to całkowita liczba "okazji" do spotkań
        przez wspólnego znajomego.
        """
        return 0.5 * sum(
            self._deg(i) * (self._deg(i) - 1)
            for i in range(self.size)
        )

    def _event_count(self, expected_value: float) -> int:
        """
        Zamienia wartość oczekiwaną zdarzeń na liczbę całkowitą.

        Przykład:
        - 15.2 daje zwykle 15, czasem 16,
        - 0.05 daje jedno zdarzenie z prawdopodobieństwem 0.05.

        Dzięki temu nie gubimy małych częstości typu ne * gamma < 1.
        """
        if expected_value <= 0:
            return 0

        base = int(expected_value)
        fraction = expected_value - base

        if random.random() < fraction:
            return base + 1

        return base

    def _weighted_choices(self, weights: List[float], k: int) -> List[int]:
        """
        Losowanie z powtórzeniami.

        Jeśli suma wag = 0, zwraca pustą listę.
        """
        total = sum(weights)

        if total <= 0 or k <= 0:
            return []

        population = list(range(self.size))
        return random.choices(population, weights=weights, k=k)

    def _step1_random_meetings(self):
        """
        1) Losowe spotkania par.

        W każdym kroku wybieramy np * r0 par wierzchołków jednostajnie losowo.
        Jeśli para nie ma jeszcze krawędzi i oba wierzchołki mają stopień < z_star,
        dodajemy krawędź.
        """
        k = self._event_count(self._num_pairs() * self.r0)

        for _ in range(k):
            u, v = random.sample(range(self.size), 2)
            self._try_add_edge(u, v)

    def _step2_neighbor_meetings(self):
        """
        2) Spotkania przez wspólnych znajomych.

        Wybieramy nm * r1 wierzchołków z prawdopodobieństwem proporcjonalnym
        do z_i * (z_i - 1). Następnie dla każdego wybranego wierzchołka
        wybieramy losową parę jego sąsiadów i próbujemy dodać między nimi krawędź.
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

            a, b = random.sample(neighbors, 2)
            self._try_add_edge(a, b)

    def _step3_edge_deletions(self):
        """
        3) Zanikanie krawędzi.

        Wybieramy ne * gamma wierzchołków z prawdopodobieństwem proporcjonalnym
        do z_i. Następnie dla każdego wybranego wierzchołka usuwamy krawędź
        do losowego sąsiada.
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

            j = random.choice(tuple(self._adj[i]))
            self._try_remove_edge(i, j)

    def _phase1_build_network(self):
        """
        Faza 1: budowanie sieci.

        Startujemy z pustego albo wstępnie zainicjalizowanego grafu.
        Wykonujemy tylko kroki 1 i 2, bez usuwania krawędzi,
        aż średni stopień osiągnie build_target_ratio * z_star.

        W artykule opisano to jako uruchamianie pierwszych dwóch kroków,
        aż wszystkie lub większość wierzchołków osiągnie stopień z_star.
        Tutaj używamy praktycznego progu średniego stopnia.
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

            # zabezpieczenie: jeśli przez wiele kroków nic się nie zmienia,
            # dalsze budowanie raczej nie ma sensu
            if stagnant_steps >= 100:
                break

            steps += 1

    def create(self) -> Dict[int, List[object]]:
        """
        Tworzy topologię zgodnie z Model II:

        phase 1:
            step1
            step2

        phase 2:
            step1
            step2
            step3
        """
        # phase 1: build network
        self._phase1_build_network()

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