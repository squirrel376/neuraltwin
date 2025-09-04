import os
from typing import Literal

import pandas as pd


def save_data(
    data: pd.DataFrame,
    path: str,
    file_type: Literal["CSV", "NDJSON", "PARQUET"],
    file_name: str,
):
    """Save DataFrame to a file."""
    os.makedirs(path, exist_ok=True)
    full_path = os.path.join(path, file_name)
    if file_type == "CSV":
        data.to_csv(full_path, index=False)
    elif file_type == "NDJSON":
        data.to_json(full_path, orient="records", lines=True)
    elif file_type == "PARQUET":
        if "timestamp" in data.columns:
            data["timestamp"] = data["timestamp"].astype("datetime64[us]")
        data.to_parquet(full_path, index=False)
