import os
import random
from datetime import datetime, timedelta

import pandas as pd
from typing import Literal
from .wagon import Wagon
import numpy as np
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet


class WagonSimulator:
    """
    Simulate sensor data and failures for a wagon over time with one measurement per day.
    """

    def __init__(self, wagon: Wagon, failure_rates: dict, failure_causes: dict):
        self.wagon = wagon
        self.failure_rates = failure_rates
        self.failure_causes = failure_causes
        self.timestamps = []
        self.failure_log = []

    def simulate(self):
        self.timestamps = pd.date_range(
            start=self.wagon.get_sensor_installation_date(),
            end=datetime.now(),
            freq="D",
        ).tolist()

        # Parts with Weibull-like failure dynamics
        parts = {
            "brakes": {"lambda0": 0.0003, "lifetime": 800, "beta": 2.0},
            "axle": {"lambda0": 0.0002, "lifetime": 1200, "beta": 1.8},
            "battery": {"lambda0": 0.0001, "lifetime": 600, "beta": 2.2},
            "cooling": {"lambda0": 0.0004, "lifetime": 500, "beta": 2.5},
        }

        # Assign initial states per part
        for part in parts:
            parts[part]["failed"] = False
            parts[part]["last_replacement"] = self.timestamps[0] - timedelta(
                days=random.randint(1, 365)
            )
            parts[part]["failures"] = []

        # Sensor baselines (healthy wagon)
        BASELINES = {
            "speed": 60,  # km/h
            "brake": 5,  # bar
            "temp": 40,  # °C
            "vibration": 2,  # mm/s
            "battery": 100,  # %
        }

        # Degradation rates per day (small, but accumulate over months/years)
        DEGRADATION_RATES = {
            "speed": -0.02,  # slower over time
            "brake": +0.005,  # braking worsens
            "temp": +0.02,  # hotter over time
            "vibration": +0.005,  # more vibrations
            "battery": -0.05,  # battery loses charge capacity faster
        }

        # Initialize sensor series
        speed, brake, temp, vibration, battery = [], [], [], [], []
        failure_state = False

        for t in self.timestamps:
            wagon_failure_probs = []
            for part, cfg in parts.items():
                if not cfg["failed"]:
                    part_age_days = (t - cfg["last_replacement"]).days
                    lam = cfg["lambda0"] * (
                        (1 + part_age_days / cfg["lifetime"]) ** cfg["beta"]
                    )
                    p_fail = min(1.0, lam)
                    failure_happens = np.random.rand() < p_fail

                    if failure_happens:
                        cfg["failed"] = True
                        repair_delay = timedelta(hours=random.randint(3, 24))
                        repair_time = t + repair_delay
                        cause = f"{part} failure"
                        cfg["failures"].append(
                            {
                                "timestamp": t,
                                "repair_time": repair_time,
                                "downtime": repair_delay,
                                "cause": cause,
                            }
                        )
                        self.failure_log.append(cfg["failures"][-1])

                wagon_failure_probs.append(cfg["failed"])

            failure_state = any(wagon_failure_probs)

            # Sensor readings — worsen over time, reset after repair
            # Add Gaussian noise for realism
            # Speed is mostly tied to axle & brakes; others tied to relevant parts
            axle_age = (t - parts["axle"]["last_replacement"]).days
            brake_age = (t - parts["brakes"]["last_replacement"]).days
            battery_age = (t - parts["battery"]["last_replacement"]).days
            cooling_age = (t - parts["cooling"]["last_replacement"]).days

            if failure_state:
                # Severe degradation during failure
                speed.append(0)
                brake.append(BASELINES["brake"] + 3 + np.random.normal(0, 0.5))
                temp.append(BASELINES["temp"] + 40 + np.random.normal(0, 5))
                vibration.append(BASELINES["vibration"] + 8 + np.random.normal(0, 2))
                battery.append(
                    max(0, (battery[-1] - np.random.uniform(0.5, 1))) if battery else 95
                )
            else:
                speed.append(
                    BASELINES["speed"]
                    + DEGRADATION_RATES["speed"] * axle_age
                    + np.random.normal(0, 0.5)
                )
                brake.append(
                    BASELINES["brake"]
                    + DEGRADATION_RATES["brake"] * brake_age
                    + np.random.normal(0, 0.1)
                )
                temp.append(
                    BASELINES["temp"]
                    + DEGRADATION_RATES["temp"] * cooling_age
                    + np.random.normal(0, 0.5)
                )
                vibration.append(
                    BASELINES["vibration"]
                    + DEGRADATION_RATES["vibration"] * axle_age
                    + np.random.normal(0, 0.2)
                )
                battery.append(
                    BASELINES["battery"]
                    + DEGRADATION_RATES["battery"] * battery_age
                    + np.random.normal(0, 0.5)
                )

            # After repair, reset part's baseline
            for part, cfg in parts.items():
                if cfg["failed"] and t >= cfg["failures"][-1]["repair_time"]:
                    cfg["failed"] = False
                    cfg["last_replacement"] = t

        # Save results
        self.simulated_time_series = pd.DataFrame(
            {
                "timestamp": self.timestamps,
                "speed": speed,
                "brake": brake,
                "temp": temp,
                "vibration": vibration,
                "battery": battery,
            }
        )
        self.simulated_time_series["id"] = self.wagon.get_id()

    def get_failures(self) -> pd.DataFrame:
        if not self.failure_log:
            dtypes = {
                "id": "string",
                "timestamp": "datetime64[ns]",
                "repair_time": "datetime64[ns]",
                "downtime": "timedelta64[ns]",
                "cause": "object",
            }
            empty_df = pd.DataFrame({col: pd.Series(dtype=dt) for col, dt in dtypes.items()})
            return empty_df
        failures = pd.DataFrame(self.failure_log)
        failures["id"] = self.wagon.get_id()
        return failures

    def get_results(self) -> pd.DataFrame:
        return pd.DataFrame(self.simulated_time_series)

    def get_training_data(self) -> pd.DataFrame:
        """Return training data with failure labels for the wagon."""
        results = self.get_results()
        failures = self.get_failures()
        results["failure"] = False
        results.loc[
            results["timestamp"].isin(failures["timestamp"]), "failure"
        ] = True
        return results

    def generate_failure_pdf(self):
        # Set PDF path per wagon
        pdf_path = os.path.join(self.output_dir, f"{self.wagon.get_id()}_failures.pdf")
        doc = SimpleDocTemplate(pdf_path, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        # PDF Title
        title = Paragraph(
            f"<b>Failure & Repair Report — Wagon {self.wagon.get_id()}</b>",
            styles["Title"],
        )
        elements.append(title)
        elements.append(Spacer(1, 16))

        # If no failures recorded, just report that
        if not self.failure_log:
            elements.append(Paragraph("No failures recorded.", styles["Normal"]))
            doc.build(elements)
            return

        # ================================
        # 1. Summarize failures per part
        # ================================
        failures_by_part = {}
        for failure in self.failure_log:
            part = failure["cause"].split()[0]  # e.g., "brakes failure" -> "brakes"
            if part not in failures_by_part:
                failures_by_part[part] = []
            failures_by_part[part].append(failure)

        # Compute summary table
        summary_data = [["Part", "Total Failures", "Total Downtime (h)", "MTBF (days)"]]
        for part, failures in failures_by_part.items():
            # Sort failures by timestamp
            sorted_failures = sorted(failures, key=lambda x: x["failure_timestamp"])

            # Calculate MTBF (Mean Time Between Failures)
            if len(sorted_failures) > 1:
                deltas = [
                    (
                        sorted_failures[i]["failure_timestamp"]
                        - sorted_failures[i - 1]["failure_timestamp"]
                    ).days
                    for i in range(1, len(sorted_failures))
                ]
                mtbf = np.mean(deltas)
            else:
                mtbf = float("nan")

            total_downtime = sum(
                [f["downtime"].total_seconds() / 3600 for f in failures]
            )

            summary_data.append(
                [
                    part.capitalize(),
                    str(len(failures)),
                    f"{total_downtime:.1f}",
                    f"{mtbf:.1f}" if not np.isnan(mtbf) else "N/A",
                ]
            )

        summary_table = Table(summary_data, colWidths=[100, 100, 140, 140])
        summary_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ]
            )
        )

        elements.append(
            Paragraph("<b>Summary of Failures by Component</b>", styles["Heading2"])
        )
        elements.append(summary_table)
        elements.append(Spacer(1, 20))

        # ================================
        # 2. Detailed failure table
        # ================================
        data = [
            [
                "Failure ID",
                "Part",
                "Failure Time",
                "Repair Time",
                "Downtime (h)",
                "Cause",
            ]
        ]
        for i, failure in enumerate(self.failure_log, 1):
            data.append(
                [
                    str(i),
                    failure["cause"].split()[0].capitalize(),
                    failure["failure_timestamp"].strftime("%Y-%m-%d %H:%M"),
                    failure["repair_time"].strftime("%Y-%m-%d %H:%M"),
                    f"{failure['downtime'].total_seconds() / 3600:.1f}",
                    failure["cause"],
                ]
            )

        detail_table = Table(data, colWidths=[60, 80, 120, 120, 80, 160])
        detail_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ]
            )
        )

        elements.append(Paragraph("<b>Detailed Failure Log</b>", styles["Heading2"]))
        elements.append(detail_table)
        elements.append(Spacer(1, 20))

        # ================================
        # 3. Footer
        # ================================
        footer = Paragraph(
            f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            styles["Normal"],
        )
        elements.append(footer)

        # Build PDF
        doc.build(elements)
