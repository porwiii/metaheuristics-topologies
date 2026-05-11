from typing import Dict, List
import os
import csv
import ray

from islands_desync.geneticAlgorithm.migrations.ray_migration import RayMigration
from islands_desync.islands.core.Emigration import Emigration
from islands_desync.islands.core.SignalActor import SignalActor


class RayMigrationPipeline(RayMigration):
    def __init__(self, islandActor, emigration: Emigration, signal_actor: SignalActor):
        super().__init__(islandActor, emigration, signal_actor)
        self.new_individuals_refs = self.islandActor.get_immigrants.remote()
        self.to_island = ray.get(self.islandActor.get_island_id.remote())

        #print("[DEBUG] RayMigrationPipeline self dict:", self.__dict__, flush=True)

        array_job_id = os.getenv("SLURM_ARRAY_JOB_ID", os.getenv("SLURM_JOB_ID", "local"))
        array_task_id = os.getenv("SLURM_ARRAY_TASK_ID", "local")

        topology = os.getenv("TOPOLOGY", "unknown_topology")
        #print(topology)

        self.delay_dir = os.path.join(
            "experiments",
            topology,
            f"job_array_{array_job_id}",
            "tasks",
            f"{topology}_task_{array_task_id}"
        )

        os.makedirs(self.delay_dir, exist_ok=True)

        self.delay_csv_path = os.path.join(self.delay_dir, "migration_delays.csv")

        if not os.path.exists(self.delay_csv_path):
            with open(self.delay_csv_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "recv_step",
                    "recv_eval",
                    "from_island",
                    "to_island",
                    "send_step",
                    "send_eval",
                    "delay_steps",
                    "delay_eval",
                    "send_timestamp",
                    "fitness"
                ])

    def receive_individuals(self, step_num: int, evaluations: int):
        new_individuals = ray.get(self.new_individuals_refs)
        self.new_individuals_refs = self.islandActor.get_immigrants.remote()

        if len(new_individuals) == 0:
            return [], None

        new_individuals, migrant_iteration_numbers, migrant_evaluations, ind_timestamps, src_island, fitness = zip(*new_individuals)
        #new_individuals, migrant_iteration_numbers, ind_timestamps, src_island, fitness = zip(*new_individuals)

        delays_eval = []
        delays_steps = []

        with open(self.delay_csv_path, "a", newline="") as f:
            writer = csv.writer(f)

            for migrant_iter, migrant_eval, timestamp, source, fit in zip(
                migrant_iteration_numbers,
                migrant_evaluations,
                ind_timestamps,
                src_island,
                fitness
            ):
                delay_steps = step_num - migrant_iter
                delay_eval = evaluations - migrant_eval

                # delay_eval = evaluations - migrant_iter
                delays_eval.append(delay_eval)
                delays_steps.append(delay_steps)

                writer.writerow([
                    step_num,
                    evaluations,
                    source,
                    self.to_island,
                    migrant_iter,
                    migrant_eval,
                    delay_steps,
                    delay_eval,
                    timestamp,
                    fit
                ])
                
                # print(
                #     f"[DELAY] recv_step={step_num}, recv_eval={evaluations}, "
                #     f"from={source}, to={self.to_island}, "
                #     f"send_step={migrant_iter}, send_eval={migrant_eval}, "
                #     f"delay_steps={delay_steps}, delay_eval={delay_eval}, "
                #     f"fitness={fit}",
                #     flush=True
                # )

        migration_at_step_num = {
            "step": step_num,
            "ev": evaluations,
            "iteration_numbers": migrant_iteration_numbers,
            "timestamps": ind_timestamps,
            "src_islands": src_island,
            "fitnesses": fitness,
            "delay_evals": delays_eval,
            "delay_steps": delays_steps
        }

        return list(new_individuals), migration_at_step_num

    # def receive_individuals(
    #     self, step_num: int, evaluations: int
    # ) :
    #     new_individuals = ray.get(self.new_individuals_refs)
    #     self.new_individuals_refs = self.islandActor.get_immigrants.remote()

    #     new_individuals, migrant_iteration_numbers, ind_timestamps, src_island, fitness = zip(*new_individuals)

    #     migration_at_step_num = {
    #         "step": step_num,
    #         "ev": evaluations,
    #         "iteration_numbers": migrant_iteration_numbers,
    #         "timestamps": ind_timestamps,
    #         "src_islands": src_island,
    #         "fitnesses": fitness,
    #     }

    #     return list(new_individuals), migration_at_step_num
