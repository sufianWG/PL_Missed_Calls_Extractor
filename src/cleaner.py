from typing import Iterable, List

from .models import MissedCallRecord


def clean_duplicates(records: Iterable[MissedCallRecord]) -> List[MissedCallRecord]:
    """Keep the latest missed call for each phone number."""
    latest_by_number = {}
    for record in records:
        existing = latest_by_number.get(record.phone_number)
        if existing is None or record.missed_at > existing.missed_at:
            latest_by_number[record.phone_number] = record

    return sorted(latest_by_number.values(), key=lambda item: item.missed_at, reverse=True)


def count_duplicate_numbers(records: Iterable[MissedCallRecord]) -> int:
    counts = {}
    for record in records:
        counts[record.phone_number] = counts.get(record.phone_number, 0) + 1
    return sum(1 for total in counts.values() if total > 1)
