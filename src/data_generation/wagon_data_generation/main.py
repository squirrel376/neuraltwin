import os
from fleet_manager import FleetManager


# -----------------------
# Global Simulation Config
# -----------------------
OUTPUT_DIR = "../../data/wagon_data"
MEASUREMENTS_OUTPUT_DIR = "../../data/wagon_data/measurements"
METADATA_OUTPUT_DIR = "../../data/wagon_data/metadata"
FAILURES_OUTPUT_DIR = "../../data/wagon_data/failures"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(MEASUREMENTS_OUTPUT_DIR, exist_ok=True)
os.makedirs(METADATA_OUTPUT_DIR, exist_ok=True)
os.makedirs(FAILURES_OUTPUT_DIR, exist_ok=True)

WAGON_TYPES = ["Boxcar", "Flatcar", "Tank Car", "Hopper", "Refrigerator Car", "Gondola"]
STATUS_OPTIONS = ["In Service", "Under Maintenance", "Decommissioned", "Reserved"]

# Base failure rates per wagon type
BASE_FAILURE_RATES = {
    "Boxcar": 0.0005,
    "Flatcar": 0.0006,
    "Tank Car": 0.0010,
    "Hopper": 0.0007,
    "Refrigerator Car": 0.0012,
    "Gondola": 0.0008,
}

# Failure causes per type
FAILURE_CAUSES = {
    "Boxcar": ["Brake Failure", "Axle Overheating", "Door Jam"],
    "Flatcar": ["Coupling Issue", "Brake Failure", "Axle Overheating"],
    "Tank Car": ["Leak Detected", "Brake Failure", "Sensor Malfunction"],
    "Hopper": ["Hatch Blockage", "Brake Failure", "Overheating Bearings"],
    "Refrigerator Car": ["Cooling System Fault", "Door Jam", "Brake Failure"],
    "Gondola": ["Structural Crack", "Brake Failure", "Axle Overheating"],
}


# -----------------------
# Run Simulation
# -----------------------
if __name__ == "__main__":
    manager = FleetManager(
        failure_rates=BASE_FAILURE_RATES,
        failure_causes=FAILURE_CAUSES,
        wagon_types=WAGON_TYPES,
        sensor_output_dir=OUTPUT_DIR,
        num_wagons=1,
    )
    manager.generate_fleet()
