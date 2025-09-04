import os
import random
from datetime import datetime
from typing import Literal
from faker import Faker
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet


class Wagon:
    def __init__(self, wagon_types: list):
        """
        Initializes a new Wagon instance. Wagons are at least 5 years old and have sensor data for maximum 5 years and minimum 1 year.

        """
        fake = Faker()

        manufacture_date = fake.date_between(start_date="-30y", end_date="-5y")
        self.data = {
            "id": f"WGN-{fake.unique.random_int(10000, 99999)}",
            "Type": random.choice(wagon_types),
            "Capacity_tons": random.randint(20, 120),
            "Length_m": round(random.uniform(8.0, 25.0), 2),
            "Width_m": round(random.uniform(2.5, 3.5), 2),
            "Height_m": round(random.uniform(2.0, 4.5), 2),
            "Operator": fake.company(),
            "Owner": fake.company(),
            "Manufacture_Date": manufacture_date.strftime("%Y-%m-%d"),
            "Sensor_Installation_Date": fake.date_between(
                start_date="-5y", end_date="-1y"
            ).strftime("%Y-%m-%d"),
        }

    def get_id(self):
        return self.data["id"]

    def get_type(self):
        return self.data["Type"]

    def get_age_years(self):
        return (
            datetime.now().year
            - datetime.strptime(self.data["Manufacture Date"], "%Y-%m-%d").year
        )

    def get_sensor_installation_date(self):
        return self.data["Sensor Installation Date"]

    def write_wagon_metadata(
        self, path: str, file_type: Literal["csv", "json", "parquet"], file_name: str
    ):
        """Writes wagon metadata to specified file format."""
        df = pd.DataFrame([self.data])
        full_path = os.path.join(path, file_name)
        if file_type == "csv":
            df.to_csv(full_path, index=False)
        elif file_type == "json":
            df.to_json(full_path, orient="records")
        elif file_type == "parquet":
            df.to_parquet(full_path, index=False)

    def generate_info_pdf(self, output_dir: str):
        """Generates static wagon info PDF."""
        pdf_path = os.path.join(output_dir, f"{self.get_id()}.pdf")
        doc = SimpleDocTemplate(pdf_path, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        title = Paragraph("<b>Railroad Wagon Information Sheet</b>", styles["Title"])
        elements.append(title)
        elements.append(Spacer(1, 12))

        data = [[key, str(value)] for key, value in self.data.items()]
        table = Table(data, colWidths=[150, 300])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ]
            )
        )
        elements.append(table)
        elements.append(Spacer(1, 12))

        footer = Paragraph(
            f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            styles["Normal"],
        )
        elements.append(footer)
        doc.build(elements)
