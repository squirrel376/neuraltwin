import os
import csv
import random
from datetime import datetime, timedelta

import pandas as pd
from wagon import Wagon
import numpy as np
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet


class WagonSimulator:
    """
    Simulate sensor data and failures for a wagon over time with one measurement per day.
    """
    def __init__(self, wagon: Wagon, failure_rates: dict, failure_causes: dict, output_dir: str):
        self.wagon = wagon
        self.failure_rates = failure_rates
        self.failure_causes = failure_causes
        self.output_dir = output_dir
        self.timestamps = []
        self.failure_log = []

    def simulate(self):
        self.timestamps = pd.date_range(
            start=self.wagon.get_sensor_installation_date(),
            end=datetime.now(),
            freq='D'
        ).tolist()

        # Define parts with base failure rates and aging parameters
        parts = {
            "brakes":     {"lambda0": 0.0003, "lifetime": 800, "beta": 2.0},
            "axle":       {"lambda0": 0.0002, "lifetime": 1200, "beta": 1.8},
            "battery":    {"lambda0": 0.0001, "lifetime": 600, "beta": 2.2},
            "cooling":    {"lambda0": 0.0004, "lifetime": 500, "beta": 2.5},
        }

        # Track state for each part
        for part in parts:
            parts[part]["failed"] = False
            parts[part]["last_replacement"] = self.timestamps[0] - timedelta(days=random.randint(1, 365))
            parts[part]["failures"] = []

        # Initialize sensor time series
        speed, brake, temp, vibration, battery = [], [], [], [], []
        failure_state = False

        for t in self.timestamps:
            # Calculate individual part failure probabilities based on time since last replacement
            wagon_failure_probs = []
            for part, cfg in parts.items():
                if not cfg["failed"]:
                    part_age_days = (t - cfg["last_replacement"]).days
                    lam = cfg["lambda0"] * ((1 + part_age_days / cfg["lifetime"]) ** cfg["beta"])
                    p_fail = min(1.0, lam)  # cap at 100%
                    failure_happens = np.random.rand() < p_fail

                    if failure_happens:
                        cfg["failed"] = True
                        repair_delay = timedelta(hours=random.randint(3, 24))
                        repair_time = t + repair_delay
                        cause = f"{part} failure"
                        cfg["failures"].append({
                            "failure_timestamp": t,
                            "repair_time": repair_time,
                            "downtime": repair_delay,
                            "cause": cause
                        })
                        self.failure_log.append(cfg["failures"][-1])

                wagon_failure_probs.append(cfg["failed"])

            # Determine overall wagon failure state
            failure_state = any(wagon_failure_probs)

            # Sensor behavior based on failure state
            if failure_state:
                speed.append(0)
                brake.append(np.random.normal(1, 0.3))
                temp.append(np.random.normal(80, 10))
                vibration.append(np.random.normal(10, 5))
                battery.append(max(0, battery[-1] - np.random.uniform(0.2, 0.5)) if battery else 95)
            else:
                speed.append(np.random.normal(60, 5))
                brake.append(np.random.normal(5, 0.5))
                temp.append(np.random.normal(40, 5))
                vibration.append(np.random.normal(2, 0.5))
                battery.append(battery[-1] - np.random.uniform(0.01, 0.05) if battery else 100)

            # Process repairs: after repair_time, reset the failed part
            for part, cfg in parts.items():
                if cfg["failed"] and t >= cfg["failures"][-1]["repair_time"]:
                    cfg["failed"] = False
                    cfg["last_replacement"] = t  # reset part age
        self.results = {
            "timestamps": self.timestamps,
            "speed": speed,
            "brake": brake,
            "temp": temp,
            "vibration": vibration,
            "battery": battery
        }
        self._write_sensor_csv(speed, brake, temp, vibration, battery)
        self.generate_failure_pdf()

    def _write_sensor_csv(self, speed, brake, temp, vibration, battery):
        csv_path = os.path.join(self.output_dir, f"{self.wagon.get_id()}_sensors.csv")
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "speed_kmh", "brake_bar", "axle_temp_C", "vibration_g", "battery_%"])
            writer.writerows(zip(self.timestamps, speed, brake, temp, vibration, battery))

    def generate_failure_pdf(self):
        # Set PDF path per wagon
        pdf_path = os.path.join(self.output_dir, f"{self.wagon.get_id()}_failures.pdf")
        doc = SimpleDocTemplate(pdf_path, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        # PDF Title
        title = Paragraph(f"<b>Failure & Repair Report — Wagon {self.wagon.get_id()}</b>", styles['Title'])
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
                    (sorted_failures[i]["failure_timestamp"] - sorted_failures[i - 1]["failure_timestamp"]).days
                    for i in range(1, len(sorted_failures))
                ]
                mtbf = np.mean(deltas)
            else:
                mtbf = float("nan")

            total_downtime = sum([f["downtime"].total_seconds() / 3600 for f in failures])

            summary_data.append([
                part.capitalize(),
                str(len(failures)),
                f"{total_downtime:.1f}",
                f"{mtbf:.1f}" if not np.isnan(mtbf) else "N/A"
            ])

        summary_table = Table(summary_data, colWidths=[100, 100, 140, 140])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))

        elements.append(Paragraph("<b>Summary of Failures by Component</b>", styles['Heading2']))
        elements.append(summary_table)
        elements.append(Spacer(1, 20))

        # ================================
        # 2. Detailed failure table
        # ================================
        data = [["Failure ID", "Part", "Failure Time", "Repair Time", "Downtime (h)", "Cause"]]
        for i, failure in enumerate(self.failure_log, 1):
            data.append([
                str(i),
                failure["cause"].split()[0].capitalize(),
                failure["failure_timestamp"].strftime("%Y-%m-%d %H:%M"),
                failure["repair_time"].strftime("%Y-%m-%d %H:%M"),
                f"{failure['downtime'].total_seconds() / 3600:.1f}",
                failure["cause"]
            ])

        detail_table = Table(data, colWidths=[60, 80, 120, 120, 80, 160])
        detail_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))

        elements.append(Paragraph("<b>Detailed Failure Log</b>", styles['Heading2']))
        elements.append(detail_table)
        elements.append(Spacer(1, 20))

        # ================================
        # 3. Footer
        # ================================
        footer = Paragraph(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal'])
        elements.append(footer)

        # Build PDF
        doc.build(elements)

