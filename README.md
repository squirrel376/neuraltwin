## NeuralTwin: The Industrial Digital Twin Agent

Transform raw, chaotic industrial sensor data into predictive, actionable intelligence using BigQuery AI.

— Submission for the BigQuery AI Hackathon —

### Summary (TL;DR)
- Industrial teams are drowning in IIoT sensor data but starving for insights.
- NeuralTwin is an end-to-end Python agent that ingests raw files (CSV/Parquet/JSON), centralizes them in BigQuery, trains a predictive failure model with PyCaret, forecasts sensor trajectories via BigQuery AI.FORECAST, and generates stakeholder-ready reports with BigQuery’s generative AI.
- Output: a monthly report that summarizes performance and clearly flags which assets are likely to fail in the next 30 days.

---

## Why it matters
- **Data heterogeneity**: measurements in CSV, failures in Parquet, metadata in JSON.
- **Modeling complexity**: building/deploying TS/classification models is hard to productionize.
- **Actionability gap**: a notebook with 95% accuracy doesn’t prevent a machine from failing.


---

## Architecture
```
Raw files (CSV/Parquet/JSON) → GCS → BigQuery tables
                                       │
                          ┌────────────┴────────────┐
                          │                         │
                   PyCaret classification       AI.FORECAST for sensors
                          │                         │
                          └────────────┬────────────┘
                                       │
              AI.GENERATE_TEXT for monthly report & next-30-day risks
                                       │
                            HTML/PDF report delivery
```

- Data lake/warehouse: Google Cloud Storage + BigQuery
- Modeling: Classification via PyCaret (current). A BigQuery ML path is an optional alternative.
- Generative AI: BigQuery AI text generation for tailored reports
- Orchestration: Python scripts / notebooks

---

## Repository map
- Data generation (synthetic IIoT + failures): `src/data_generation/wagon_data_generation/*.py`
- Classification notebooks (agent + simulation): `src/classification/agent.ipynb`, `src/classification/run_simulation.ipynb`
- Example output report: `report_for_Smith_Ltd.html`

> Kaggle requirement: All core code is in this repo and the notebooks are directly viewable here.

---

## Setup

### Python environment
We use `pyproject.toml` with pinned deps:

```bash
# macOS/Linux
python3 -m venv .venv && source .venv/bin/activate
pip install -U pip
pip install -e .
```

Key deps: `google-cloud-bigquery`, `pandas-gbq`, `pyarrow`, `pycaret`, `fpdf2`/`reportlab`.

---

## Quickstart (end-to-end)

### A) Generate synthetic data (optional)
Use our fleet simulator to produce realistic sensor and failure datasets.

```bash
python src/data_generation/wagon_data_generation/main.py
```

Outputs: CSVs for sensor time series, PDFs for failures/metadata.

### B) Run the notebooks
- Open `src/classification/agent.ipynb` or `src/classification/run_simulation.ipynb` and execute the cells.
- These notebooks perform data prep, train the classifier with PyCaret, make predictions, and generate the report.

---

## Notebooks and scripts
- `src/classification/agent.ipynb`: end-to-end agent workflow (ingest → train → predict → report) with PyCaret classification
- `src/classification/run_simulation.ipynb`: quick E2E with PyCaret for baseline modeling and predictions executed outside BigQuery
- `src/data_generation/wagon_data_generation/*.py`: synthetic IIoT and failure generation

---

## AI and BigQuery functions used (from notebooks)
- Forecasting: `AI.FORECAST`
- Generative report: `AI.GENERATE` (Vertex AI via BigQuery connection)
- Classification: PyCaret (`setup`, `compare_models`, `predict_model`)

---

## Notes on the simulator (for synthetic datasets)
The simulator models component wear and sensor drift using:
- Parts with Weibull-like failure dynamics (`lambda0`, `lifetime`, `beta`)
- Healthy baselines for speed/brake/temp/vibration/battery
- Small per-day degradation rates to emulate drift

You can tune these in `src/data_generation/wagon_data_generation/wagon_simulator.py`.

---