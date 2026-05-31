import re
from pathlib import Path
from typing import Iterable, List

from .models import MissedCallRecord
from .ocr import image_to_text

# Targets unsaved callers because saved contacts usually appear as names, not phone-number patterns.
PHONE_PATTERN = re.compile(
    r"(?:\+?1[\s\-.]*)?\(?\d{3}\)?[\s\-.]+\d{3}[\s\-.]+\d{4}"
)

DATE_TIME_PATTERN = re.compile(
    r"(?P<date>\d{1,2}/\d{1,2}/\d{4})\s*(?:at|@)?\s*(?P<time>\d{1,2}:\d{2}\s*[AP]M)",
    re.IGNORECASE,
)


def normalize_phone(value: str) -> str:
    digits = re.sub(r"\D", "", value)
    if len(digits) == 10:
        digits = "1" + digits
    if len(digits) == 11 and digits.startswith("1"):
        return f"+1 {digits[1:4]}-{digits[4:7]}-{digits[7:11]}"
    return value.strip()


def normalize_date(value: str) -> str:
    parts = value.split("/")
    if len(parts) != 3:
        return value.strip()
    month, day, year = parts
    return f"{int(month)}/{int(day)}/{year}"


def normalize_time(value: str) -> str:
    return re.sub(r"\s+", " ", value.upper()).strip()


def parse_text(text: str, source_file: str = "") -> List[MissedCallRecord]:
    records: List[MissedCallRecord] = []
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    for index, line in enumerate(lines):
        phone_match = PHONE_PATTERN.search(line)
        if not phone_match:
            continue

        # Phone Link date/time may OCR into the same line or a nearby line on the right side.
        search_area = " ".join(lines[max(0, index - 2): index + 6])
        date_match = DATE_TIME_PATTERN.search(search_area)
        if not date_match:
            continue

        try:
            record = MissedCallRecord(
                phone_number=normalize_phone(phone_match.group(0)),
                missed_call_date=normalize_date(date_match.group("date")),
                missed_call_time=normalize_time(date_match.group("time")),
                source_file=source_file,
            )
            # Validate date/time format early.
            record.missed_at
            records.append(record)
        except Exception:
            continue

    return records


def extract_from_images(image_paths: Iterable[str]) -> List[MissedCallRecord]:
    records: List[MissedCallRecord] = []
    for image_path in image_paths:
        text = image_to_text(image_path)
        records.extend(parse_text(text, source_file=Path(image_path).name))
    return records
