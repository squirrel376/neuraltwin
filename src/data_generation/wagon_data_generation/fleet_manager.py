from collections import defaultdict
from typing import Literal

import pandas as pd

from src.data_generation.utils import save_data
from .wagon import Wagon
from .wagon_simulator import WagonSimulator


class FleetManager:
    def __init__(
        self,
        failure_rates: dict,
        failure_causes: dict,
        wagon_types: list,
        sensor_output_dir: str,
        metadata_output_dir: str,
        failure_output_dir: str,
        num_wagons: int,
        n_future_days: int = 30
    ):
        self.num_wagons = num_wagons
        self.sensor_output_dir = sensor_output_dir
        self.metadata_output_dir = metadata_output_dir
        self.failure_output_dir = failure_output_dir
        self.failure_rates = failure_rates
        self.wagon_types = wagon_types
        self.failure_causes = failure_causes
        self.n_future_days = n_future_days

        self.wagons: list[Wagon] = []
        self.simulators: list[WagonSimulator] = []
        self.failure_stats = defaultdict(list)

    def generate_wagons(self):
        self.wagons = [Wagon(self.wagon_types) for _ in range(self.num_wagons)]

    def run_simulation(self):
        for wagon in self.wagons:
            sim = WagonSimulator(
                wagon,
                self.failure_rates,
                self.failure_causes,
            )
            sim.simulate()
            self.simulators.append(sim)

    def save_historical_simulation_results(self, file_type: Literal["csv", "json", "parquet"]):
        for sim in self.simulators:
            historic_data = sim.simulated_time_series[
                sim.simulated_time_series['timestamp'] <= pd.Timestamp.now() - pd.Timedelta(days=self.n_future_days)
            ]
            save_data(
                historic_data,
                self.sensor_output_dir,
                file_type=file_type,
                file_name=f"{sim.wagon.get_id()}_sensors.{file_type}",
            )

    def get_all_failures(self) -> pd.DataFrame:
        all_failures = pd.concat([sim.get_failures() for sim in self.simulators], ignore_index=True)
        return all_failures

    def get_future_failures(self) -> pd.DataFrame:
        all_failures = self.get_all_failures()
        future_failures = all_failures[
            all_failures['timestamp'] > pd.Timestamp.now() - pd.Timedelta(days=self.n_future_days)
        ]
        return future_failures

    def save_historical_failure_results(self, file_type: Literal["csv", "json", "parquet"], one_file: bool):
        """Save historical failure results. 'Historic' refers to data up to n_future_days in the past."""
        if one_file:
            combined_failures = self.get_all_failures()
            historic_failures = combined_failures[
                combined_failures['timestamp'] <= pd.Timestamp.now() - pd.Timedelta(days=self.n_future_days)
            ]
            save_data(
                historic_failures,
                self.failure_output_dir,
                file_type=file_type,
                file_name=f"combined_failures.{file_type}",
            )
            return
        
        for sim in self.simulators:
            all_failures = sim.get_failures()
            historic_failures = all_failures[
                all_failures['timestamp'] <= pd.Timestamp.now() - pd.Timedelta(days=self.n_future_days)
            ]
            save_data(
                historic_failures,
                self.failure_output_dir,
                file_type=file_type,
                file_name=f"{sim.wagon.get_id()}_failures.{file_type}",
            )

    def save_future_failures_results(self, file_type: Literal["csv", "json", "parquet"], path: str):
        """Save all future failures into a single file. 'Future' refers to all data after n_future_days in the past."""
        combined_failures = pd.concat([sim.get_failures() for sim in self.simulators], ignore_index=True)
        future_failures = combined_failures[
            combined_failures['timestamp'] > pd.Timestamp.now() - pd.Timedelta(days=self.n_future_days)
        ]
        save_data(
            future_failures,
            path,
            file_type=file_type,
            file_name=f"combined_future_failures.{file_type}",
        )

    def save_metadata_single_files(self, file_type: Literal["csv", "json", "parquet"]):
        for wagon in self.wagons:
            save_data(
                wagon.data,
                self.metadata_output_dir,
                file_type=file_type,
                file_name=f"{wagon.get_id()}_metadata.{file_type}",
            )

    def save_metadata_one_file(self, file_type: Literal["csv", "json", "parquet"]):
        combined_metadata = pd.DataFrame([wagon.data for wagon in self.wagons])
        save_data(
            combined_metadata,
            self.metadata_output_dir,
            file_type=file_type,
            file_name=f"combined_metadata.{file_type}",
        )

    def generate_fleet(self):
        self.generate_wagons()
        self.run_simulation()

    def get_historic_fleet_training_data(self) -> pd.DataFrame:
        # Combine all historic wagon results into a single DataFrame, including wagon id and failure column
        all_training_data = self.get_fleet_training_data()
        historic_training_data = all_training_data[
            all_training_data['timestamp'] < pd.Timestamp.now() - pd.Timedelta(days=self.n_future_days)
        ]
        return historic_training_data

    def get_fleet_training_data(self) -> pd.DataFrame:
        # Combine all wagon results into a single DataFrame, including wagon id and failure column

        all_results = pd.concat(
            [sim.get_training_data() for sim in self.simulators], ignore_index=True
        )
        all_results["failure"] = all_results["failure"].astype(float)
        return all_results
