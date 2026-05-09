import json
import sys
from datetime import datetime
import os
os.environ["RAY_DEDUP_LOGS"] = "0"
import ray
from islands.core.IslandRunner import IslandRunner
from islands.selectAlgorithm import RandomSelect
from islands.topologies import RingTopology

from islands_desync.geneticAlgorithm.run_hpc.run_algorithm_params import (
    RunAlgorithmParams,
)
from islands_desync.islands.topologies.TorusTopology import TorusTopology
from islands_desync.islands.topologies.CompleteTopology import CompleteTopology
from islands_desync.islands.topologies.ERTopology import ERTopology
from islands_desync.islands.topologies.ScaleFreeTopology import ScaleFreeTopology
from islands_desync.islands.topologies.MeetingTopology import MeetingTopology
 

def main():
    print("parametry wej do start.py:")
    for i in range(1, len(sys.argv)):
        print(f"{i} - {sys.argv[i]}")

    if sys.argv[2] != " ":
        ray.init(address="auto")

    #topol = "ring"
    #topol = "torus"
    #topol = "complete"
    #topol = "er"
    topol=sys.argv[1]
    strateg=sys.argv[2]

    common_kwargs = dict(
        island_count=int(sys.argv[5]),
        number_of_emigrants=int(sys.argv[6]),
        migration_interval=int(sys.argv[7]),
        dda=sys.argv[3],
        tta=sys.argv[4],
        series_number=1,
        topology=topol,
        strategy=strateg,
    )

    if topol == "scale_free":
        params = RunAlgorithmParams(
            **common_kwargs,
            m0=int(sys.argv[8]) if len(sys.argv) > 8 and sys.argv[8] else None,
            m=int(sys.argv[9]) if len(sys.argv) > 9 and sys.argv[9] else None,
            seed=int(sys.argv[10]) if len(sys.argv) > 10 and sys.argv[10] else None,
        )

    elif topol == "meeting":
        params = RunAlgorithmParams(
            **common_kwargs,
            z_star=int(sys.argv[8]) if len(sys.argv) > 8 and sys.argv[8] else None,
            n_steps=int(sys.argv[9]) if len(sys.argv) > 9 and sys.argv[9] else None,
            r0=float(sys.argv[10]) if len(sys.argv) > 10 and sys.argv[10] else None,
            r1=float(sys.argv[11]) if len(sys.argv) > 11 and sys.argv[11] else None,
            gamma=float(sys.argv[12]) if len(sys.argv) > 12 and sys.argv[12] else None,
            build_target_ratio=float(sys.argv[13]) if len(sys.argv) > 13 and sys.argv[13] else 1.0,
            seed=int(sys.argv[14]) if len(sys.argv) > 14 and sys.argv[14] else None,
        )

    else:
        params = RunAlgorithmParams(
            **common_kwargs,
            seed=int(sys.argv[8]) if len(sys.argv) > 8 and sys.argv[8] else None,
        )

    # params = RunAlgorithmParams(
    #     island_count=int(sys.argv[5]),
    #     number_of_emigrants=int(sys.argv[6]),
    #     migration_interval=int(sys.argv[7]),
    #     dda=sys.argv[3],
    #     tta=sys.argv[4],
    #     series_number=1,
    #     topology=topol,
    #     strategy=strateg,
    #     m0=int(sys.argv[8]) if len(sys.argv) > 8 and sys.argv[8] else None,
    #     m=int(sys.argv[9]) if len(sys.argv) > 9 and sys.argv[9] else None,

    #     z_star=int(sys.argv[10]) if len(sys.argv) > 10 and sys.argv[10] else None,
    #     n_steps=int(sys.argv[11]) if len(sys.argv) > 11 and sys.argv[11] else None,
    #     npr0=int(sys.argv[12]) if len(sys.argv) > 12 and sys.argv[12] else None,
    #     nmr1=int(sys.argv[13]) if len(sys.argv) > 13 and sys.argv[13] else None,
    #     ne_gamma=int(sys.argv[14]) if len(sys.argv) > 14 and sys.argv[14] else None,
    #     seed=int(sys.argv[15]) if len(sys.argv) > 15 and sys.argv[15] else None
    # )

    if topol=="torus":
        computation_refs = IslandRunner(TorusTopology, RandomSelect, params).create()
    if topol=="ring":
        computation_refs = IslandRunner(RingTopology, RandomSelect, params).create()
    if topol=="complete":
        computation_refs = IslandRunner(CompleteTopology, RandomSelect, params).create()
    if topol=="er":
        computation_refs = IslandRunner(ERTopology, RandomSelect, params).create()
    if topol=="scale_free":
        computation_refs = IslandRunner(ScaleFreeTopology, RandomSelect, params).create()
    if topol=="meeting":
        computation_refs = IslandRunner(MeetingTopology, RandomSelect, params).create()

    print("w Start_cyf - przed ray.get")

    results = ray.get(computation_refs)

    iterations = {result["island"]: result for result in results}

    with open(
        "logs/"
        + "iterations_per_second"
        + datetime.now().strftime("%m-%d-%Y_%H%M")
        + ".json",
        "w",
    ) as f:
        json.dump(iterations, f)


if __name__ == "__main__":
    main()
