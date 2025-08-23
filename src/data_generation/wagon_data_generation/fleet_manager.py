from collections import defaultdict
from wagon import Wagon
from wagon_simulator import WagonSimulator


class FleetManager:
    def __init__(self, failure_rates: dict, failure_causes: dict, wagon_types: list, status_options: list, output_dir: str, num_wagons=5):
        self.num_wagons = num_wagons
        self.output_dir = output_dir
        self.failure_rates = failure_rates
        self.wagon_types = wagon_types
        self.status_options = status_options
        self.failure_causes = failure_causes

        self.wagons = []
        self.simulators = []
        self.failure_stats = defaultdict(list)

    def generate_wagons(self):
        self.wagons = [
            Wagon(self.wagon_types, self.status_options, self.output_dir)
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

    def validate_failures(self):
        print("\n=== FAILURE VALIDATION REPORT ===")
        total_steps = self.simulators[0].hours * 60 / self.simulators[0].freq_minutes
        for wagon_type in self.wagon_types:
            num_wagons_type = sum(1 for w in self.wagons if w.get_type() == wagon_type)
            expected = num_wagons_type * total_steps * self.failure_rates[wagon_type]
            observed = sum(self.failure_stats[wagon_type])
            print(f"{wagon_type:<20} | Wagons: {num_wagons_type:2d} | "
                  f"Expected Failures ≈ {expected:.1f} | Observed: {observed}")

    def generate_fleet(self):
        self.generate_wagons()
        self.run_simulation()
        self.validate_failures()
