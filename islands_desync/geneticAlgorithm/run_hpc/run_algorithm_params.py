import dataclasses


@dataclasses.dataclass
class RunAlgorithmParams:
    island_count: int
    number_of_emigrants: int
    migration_interval: int
    dda: str
    tta: str
    series_number: int
    topology: str
    strategy: str

    # Optional params for ScaleFreeTopology:
    m0: int | None = None
    m: int | None = None

    # Optional params for MeetingTopology
    z_star: int | None = None
    n_steps: int | None = None
    npr0: int | None = None
    nmr1: int | None = None
    ne_gamma: int | None = None
    gamma: float = 1.0
    seed: int | None = None
