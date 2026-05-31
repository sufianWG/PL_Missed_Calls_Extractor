from datetime import datetime
from pathlib import Path
from typing import Iterable

import pandas as pd

from .models import MissedCallRecord


EXPORT_COLUMNS = ["PhoneNumber", "Missed Call Date", "Missed Call Time"]


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def extracted_dir() -> Path:
    folder = project_root() / "extracted"
    folder.mkdir(exist_ok=True)
    return folder


def build_output_path(file_format: str) -> Path:
    suffix = "xlsx" if file_format.lower() == "xlsx" else "csv"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return extracted_dir() / f"missed_calls_{stamp}.{suffix}"


def export_records(records: Iterable[MissedCallRecord], file_format: str = "xlsx") -> Path:
    rows = [record.to_export_row() for record in records]
    df = pd.DataFrame(rows, columns=EXPORT_COLUMNS)
    output_path = build_output_path(file_format)

    if file_format.lower() == "csv":
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
    else:
        df.to_excel(output_path, index=False)

    return output_path
