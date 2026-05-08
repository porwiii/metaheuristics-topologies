import time
from typing import List
import os
import ray

from islands_desync.geneticAlgorithm.run_hpc.run_algorithm_params import (
    RunAlgorithmParams,
)
from islands_desync.islands.core.Island import Island
from islands_desync.islands.core.SignalActor import SignalActor
from islands_desync.islands.topologies.TorusTopology import TorusTopology
from islands_desync.islands.topologies.ScaleFreeTopology import ScaleFreeTopology
from islands_desync.islands.topologies.MeetingTopology import MeetingTopology

from experiments_interpretations.topology_analysis import save_topology_analysis_from_adj


class IslandRunner:
    def __init__(self, CreateTopology, SelectAlgorithm, params: RunAlgorithmParams):
        self.CreateTopology = CreateTopology
        self.SelectAlgorithm = SelectAlgorithm
        self.params: RunAlgorithmParams = params

    def create(self) -> List[ray.ObjectRef]:
        islands = [
            Island.remote(i, self.SelectAlgorithm())
            for i in range(self.params.island_count)
        ]

        # budujemy topologię; dla ScaleFreeTopology podajemy też m0 i m
        if self.CreateTopology is ScaleFreeTopology:
            topology_obj = self.CreateTopology(
                self.params.island_count,
                self.params.m0,
                self.params.m,
                lambda i: islands[i]
            )

        elif self.CreateTopology is MeetingTopology:
            topology_obj = self.CreateTopology(
                size=self.params.island_count,
                z_star=self.params.z_star,
                n_steps=self.params.n_steps,
                npr0=self.params.npr0,
                nmr1=self.params.nmr1,
                ne_gamma=self.params.ne_gamma,
                seed=self.params.seed,
                create_object_method=lambda i: islands[i]
            )
        
        else:
            topology_obj = self.CreateTopology(
                self.params.island_count, lambda i: islands[i]
            )

        print("\n\n\n TOPOLOGIA \n\n",topology_obj.__dict__,"\n\n\n\n\n")

        if isinstance(topology_obj, TorusTopology):
            topology = topology_obj.create(5, self.params.island_count // 5)
        else:
            topology = topology_obj.create()

        # analiza wygenerowanej topologii
        array_id = os.getenv("SLURM_ARRAY_TASK_ID", "local")

        run_dir = os.path.join(
            "results",
            f"{self.params.topology}"
            f"_seed_{self.params.seed}"
            f"_job_{array_id}"
        )

        if hasattr(topology_obj, "_adj"):
            save_topology_analysis_from_adj(topology_obj._adj, self.params, 
                                            output_dir=run_dir,
                                            filename_prefix=self.CreateTopology.__name__)
        else:
            print("No topology analysis")
        #     save_topology_analysis_from_actor_topology(topology, islands, self.params)

        # # tymczasowy debug
        # print("TYPE:", type(topology))
        # print("LEN:", len(topology))
        # for k, v in list(topology.items())[:3]:
        #     print(f"Node {k}:")
        #     print("  neighbors:", v)
        #     print("  types:", [type(x) for x in v])

        signal_actor = SignalActor.remote(self.params.island_count)

        computations = [
            ray.get(
                islands[0].start.remote(islands[0], topology[0], self.params, signal_actor)
            )
        ]

        time.sleep(15)

        computations.extend(
            ray.get(
                [
                    island.start.remote(island, topology[island_id], self.params, signal_actor)
                    for island_id, island in enumerate(islands[1:])
                ]
            )
        )

        return [computation.start.remote() for computation in computations]
