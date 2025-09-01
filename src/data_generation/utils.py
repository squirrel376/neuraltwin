import os
from typing import Literal

import pandas as pd


def save_data(
    data: pd.DataFrame,
    path: str,
    file_type: Literal["csv", "json", "parquet"],
    file_name: str,
):
    """Save DataFrame to a file."""
    os.makedirs(path, exist_ok=True)
    full_path = os.path.join(path, file_name)
    if file_type == "csv":
        data.to_csv(full_path, index=False)
    elif file_type == "json":
        data.to_json(full_path, orient="records")
    elif file_type == "parquet":
        data.to_parquet(full_path, index=False)
