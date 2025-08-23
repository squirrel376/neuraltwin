import os
import random
from datetime import datetime
from faker import Faker
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet


class Wagon:
    def __init__(self, wagon_types: list, output_dir: str):
        """
        Initializes a new Wagon instance. Wagons are at least 5 years old and have sensor data for maximum 5 years and minimum 1 year.

        """
        fake = Faker()
        self.output_dir = output_dir

        manufacture_date = fake.date_between(start_date="-30y", end_date="-5y")
        self.data = {
            "Wagon ID": f"WGN-{fake.unique.random_int(10000, 99999)}",
            "Type": random.choice(wagon_types),
            "Capacity (tons)": random.randint(20, 120),
            "Length (m)": round(random.uniform(8.0, 25.0), 2),
            "Width (m)": round(random.uniform(2.5, 3.5), 2),
            "Height (m)": round(random.uniform(2.0, 4.5), 2),
            "Operator": fake.company(),
            "Owner": fake.company(),
            "Manufacture Date": manufacture_date.strftime("%Y-%m-%d"),
            "Sensor Installation Date": fake.date_between(start_date="-5y", end_date="-1y").strftime("%Y-%m-%d"),
        }

    def get_id(self):
        return self.data["Wagon ID"]

    def get_type(self):
        return self.data["Type"]

    def get_age_years(self):
        return datetime.now().year - datetime.strptime(self.data["Manufacture Date"], "%Y-%m-%d").year
    
    def get_sensor_installation_date(self):
        return self.data["Sensor Installation Date"]

    def generate_info_pdf(self):
        """Generates static wagon info PDF."""
        pdf_path = os.path.join(self.output_dir, f"{self.get_id()}.pdf")
        doc = SimpleDocTemplate(pdf_path, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        title = Paragraph(f"<b>Railroad Wagon Information Sheet</b>", styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 12))

        data = [[key, str(value)] for key, value in self.data.items()]
        table = Table(data, colWidths=[150, 300])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 12))

        footer = Paragraph(
            f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            styles['Normal']
        )
        elements.append(footer)
        doc.build(elements)
