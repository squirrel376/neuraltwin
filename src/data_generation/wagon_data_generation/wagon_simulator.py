import os
import csv
import random
from datetime import datetime, timedelta
from wagon import Wagon
import numpy as np
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet


class WagonSimulator:
    def __init__(self, wagon: Wagon, failure_rates: dict, failure_causes: dict, output_dir: str, hours=200, freq_minutes=30):
        self.wagon = wagon
        self.failure_rates = failure_rates
        self.failure_causes = failure_causes
        self.output_dir = output_dir
        self.hours = hours
        self.freq_minutes = freq_minutes
        self.timestamps = []
        self.failure_log = []

    def simulate(self):
        """Simulate sensors & failures for a single wagon."""
        wagon_type = self.wagon.get_type()
        age_years = self.wagon.get_age_years()
        base_rate = self.failure_rates[wagon_type]
        steps = int((self.hours * 60) / self.freq_minutes)
        failure_state = False
        repair_time = 0

        speed, brake, temp, vibration, battery = [], [], [], [], []

        for step in range(steps):
            t = datetime.now() + timedelta(minutes=step * self.freq_minutes)
            self.timestamps.append(t)

            # Failure probability increases with age
            failure_prob = base_rate * (1 + age_years / 20)
            failure_happens = (not failure_state) and np.random.rand() < failure_prob

            if failure_happens:
                failure_state = True
                repair_delay = random.randint(3, 20)
                repair_time = step + repair_delay
                cause = random.choice(self.failure_causes[wagon_type])
                self.failure_log.append({
                    "start": t,
                    "repair": t + timedelta(minutes=repair_delay * self.freq_minutes),
                    "downtime": repair_delay * self.freq_minutes,
                    "cause": cause
                })

            # Sensor behavior depends on failure state
            if failure_state:
                speed.append(0)
                brake.append(np.random.normal(1, 0.3))
                temp.append(np.random.normal(80, 10))
                vibration.append(np.random.normal(10, 5))
                battery.append(max(0, battery[-1] - np.random.uniform(0.1, 0.5)) if battery else 95)
            else:
                speed.append(np.random.normal(60, 5))
                brake.append(np.random.normal(5, 0.5))
                temp.append(np.random.normal(40, 5))
                vibration.append(np.random.normal(2, 0.5))
                battery.append(battery[-1] - np.random.uniform(0.01, 0.05) if battery else 100)

            # Complete repair if time passed
            if failure_state and step >= repair_time:
                failure_state = False

        # Write CSV for sensor data
        self._write_sensor_csv(speed, brake, temp, vibration, battery)

    def _write_sensor_csv(self, speed, brake, temp, vibration, battery):
        csv_path = os.path.join(self.output_dir, f"{self.wagon.get_id()}_sensors.csv")
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "speed_kmh", "brake_bar", "axle_temp_C", "vibration_g", "battery_%"])
            writer.writerows(zip(self.timestamps, speed, brake, temp, vibration, battery))

    def generate_failure_pdf(self):
        pdf_path = os.path.join(self.output_dir, f"{self.wagon.get_id()}_failures.pdf")
        doc = SimpleDocTemplate(pdf_path, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        title = Paragraph(f"<b>Failure & Repair Report — {self.wagon.get_id()}</b>", styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 12))

        if not self.failure_log:
            elements.append(Paragraph("No failures recorded during the simulation.", styles["Normal"]))
        else:
            data = [["Failure ID", "Start Time", "Repair Time", "Downtime (min)", "Cause"]]
            for i, failure in enumerate(self.failure_log, 1):
                data.append([
                    str(i),
                    failure["start"].strftime("%Y-%m-%d %H:%M"),
                    failure["repair"].strftime("%Y-%m-%d %H:%M"),
                    str(failure["downtime"]),
                    failure["cause"]
                ])
            table = Table(data, colWidths=[70, 120, 120, 100, 150])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            elements.append(table)

        footer = Paragraph(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal'])
        elements.append(Spacer(1, 12))
        elements.append(footer)
        doc.build(elements)
