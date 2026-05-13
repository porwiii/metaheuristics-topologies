import json
import random
from typing import Dict, List
import os
import csv

from islands_desync.geneticAlgorithm.migrations.Migration import Migration
from islands_desync.geneticAlgorithm.solution.float_island_solution import (
    FloatIslandSolution,
)


class QueueMigration(Migration):
    def __init__(self, island, channel, rabbitmq_delays, number_of_islands, task_dir):
        super().__init__()
        self.island = island
        self.channel = channel
        self.rabbitmq_delays = rabbitmq_delays
        self.number_of_islands = number_of_islands
        self.task_dir = task_dir

        print(f"[DEBUG] QueueMigration init: island={self.island}", flush=True)
        print(f"[DEBUG] delay_csv_path={self.delay_csv_path}", flush=True)

        if self.task_dir is not None:
            os.makedirs(self.task_dir, exist_ok=True)
            self.delay_csv_path = os.path.join(self.task_dir, "migration_delays.csv")

            if not os.path.exists(self.delay_csv_path):
                with open(self.delay_csv_path, "w", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        "step",
                        "recv_eval",
                        "from_island",
                        "to_island",
                        "send_eval",
                        "delay_eval",
                        "fitness"
                    ])
        else:
            self.delay_csv_path = None


    def migrate_individuals(
        self, individuals_to_migrate, iteration_number, island_number
    ):
        for i in individuals_to_migrate:
            destination = random.choice(
                [
                    i
                    for i in range(0, self.number_of_islands)
                    if i != self.island
                    and self.rabbitmq_delays[str(self.island)][i] != -1
                ]
            )
            self.channel.basic_publish(
                exchange="",
                routing_key=f"island-from-{self.island}-to-{destination}",
                body=json.dumps(i.__dict__),
            )

    def receive_individuals(
        self, step_num: int, evaluations: int
    ) :
        print(
            f"[DEBUG] receive_individuals called: "
            f"island={self.island}, step={step_num}, eval={evaluations}",
            flush=True
        )
        new_individuals = []
        emigration_at_step_num = None
        for i in range(0, 5):
            method, properties, body = self.channel.basic_get(f"island-{self.island}")
            if body:
                data_str = body.decode("utf-8")
                data = json.loads(data_str)

                send_eval = data["from_evaluation"]
                delay_eval = evaluations - send_eval

                if self.delay_csv_path is not None:
                    with open(self.delay_csv_path, "a", newline="") as f:
                        writer = csv.writer(f)
                        writer.writerow([
                            step_num,
                            evaluations,
                            data["from_island"],
                            self.island,
                            send_eval,
                            delay_eval,
                            data["objectives"][0],
                        ])

                emigration_at_step_num = {
                    "step": step_num,
                    "ev": evaluations,
                    "fitn": data["objectives"][0],
                    "var": data["variables"],
                    "from_isl": data["from_island"],
                    "from_eval": data["from_evaluation"],
                    "to_isl": self.island,
                    "delay_eval": delay_eval,
                }

                print(
                    f"[DELAY] to={self.island}, "
                    f"from={data['from_island']}, "
                    f"recv_eval={evaluations}, "
                    f"send_eval={data['from_evaluation']}, "
                    f"delay_eval={delay_eval}"
                )

            
                # emigration_at_step_num = {
                #     "step": step_num,
                #     "ev": evaluations,
                #     "fitn": data["objectives"][0],
                #     "var": data["variables"],
                #     "from_isl": data["from_island"],
                #     "from_eval": data["from_evaluation"],
                # }

                float_solution = FloatIslandSolution(
                    data["lower_bound"],
                    data["upper_bound"],
                    data["number_of_variables"],
                    data["number_of_objectives"],
                    constraints=data["constraints"],
                    variables=data["variables"],
                    objectives=data["objectives"],
                    from_island=data["from_island"],
                    from_evaluation=data["from_evaluation"],
                )

                float_solution.objectives = data["objectives"]

                float_solution.variables = data["variables"]
                float_solution.number_of_constraints = data["number_of_constraints"]

                new_individuals.append(float_solution)

        return new_individuals, emigration_at_step_num
