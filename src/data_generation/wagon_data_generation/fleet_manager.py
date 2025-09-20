from collections import defaultdict
import os
from typing import Literal

import pandas as pd

from src.data_generation.utils import save_data
from .wagon import Wagon
from .wagon_simulator import WagonSimulator
from faker import Faker


class FleetManager:
    def __init__(
        self,
        wagon_types: list,
        output_dir: str,
        num_wagons: int,
        n_operators: int,
        n_future_days: int = 30,
    ):
        self.num_wagons = num_wagons
        self.output_dir = output_dir
        self.sensor_output_dir = output_dir + "/measurements"
        self.metadata_output_dir = output_dir + "/metadata"
        self.failure_output_dir = output_dir + "/failures"
        self.wagon_types = wagon_types
        self.n_future_days = n_future_days
        self.n_operators = n_operators

        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.sensor_output_dir, exist_ok=True)
        os.makedirs(self.metadata_output_dir, exist_ok=True)
        os.makedirs(self.failure_output_dir, exist_ok=True)

        fake = Faker()
        self.wagon_operators = [fake.company() for _ in range(n_operators)] 
        self.wagons: list[Wagon] = []
        self.simulators: list[WagonSimulator] = []
        self.failure_stats = defaultdict(list)

    def generate_wagons(self):
        self.wagons = [Wagon(self.wagon_types, wagon_operators=self.wagon_operators) for _ in range(self.num_wagons)]

    def run_simulation(self):
        for wagon in self.wagons:
            sim = WagonSimulator(wagon)
            sim.simulate()
            self.simulators.append(sim)

    def save_historical_simulation_results(self, file_type: Literal["CSV", "NDJSON", "PARQUET"]):
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

    def save_historical_failure_results(self, file_type: Literal["CSV", "NDJSON", "PARQUET"], one_file: bool):
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

    def save_future_failures_results(self, file_type: Literal["CSV", "NDJSON", "PARQUET"]):
        """Save all future failures into a single file. 'Future' refers to all data after n_future_days in the past."""
        combined_failures = pd.concat([sim.get_failures() for sim in self.simulators], ignore_index=True)
        future_failures = combined_failures[
            combined_failures['timestamp'] > pd.Timestamp.now() - pd.Timedelta(days=self.n_future_days)
        ]
        save_data(
            future_failures,
            self.output_dir,
            file_type=file_type,
            file_name=f"combined_future_failures.{file_type}",
        )

    def save_metadata_single_files(self, file_type: Literal["CSV", "NDJSON", "PARQUET"]):
        for wagon in self.wagons:
            save_data(
                wagon.data,
                self.metadata_output_dir,
                file_type=file_type,
                file_name=f"{wagon.get_id()}_metadata.{file_type}",
            )

    def save_metadata_one_file(self, file_type: Literal["CSV", "NDJSON", "PARQUET"]):
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
