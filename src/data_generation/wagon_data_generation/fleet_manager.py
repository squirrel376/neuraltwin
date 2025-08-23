from collections import defaultdict
from wagon import Wagon
from wagon_simulator import WagonSimulator


class FleetManager:
    def __init__(self, failure_rates: dict, failure_causes: dict, wagon_types: list, output_dir: str, num_wagons: int):
        self.num_wagons = num_wagons
        self.output_dir = output_dir
        self.failure_rates = failure_rates
        self.wagon_types = wagon_types
        self.failure_causes = failure_causes

        self.wagons = []
        self.simulators = []
        self.failure_stats = defaultdict(list)

    def generate_wagons(self):
        self.wagons = [
            Wagon(self.wagon_types, self.output_dir)
            for _ in range(self.num_wagons)
        ]

    def run_simulation(self):
        for wagon in self.wagons:
            sim = WagonSimulator(
                wagon,
                self.failure_rates,
                self.failure_causes,
                self.output_dir
            )
            wagon.generate_info_pdf()
            sim.simulate()
            sim.generate_failure_pdf()
            self.simulators.append(sim)
            self.failure_stats[wagon.get_type()].append(len(sim.failure_log))

    def generate_fleet(self):
        self.generate_wagons()
        self.run_simulation()
