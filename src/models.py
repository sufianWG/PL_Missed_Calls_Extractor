from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class MissedCallRecord:
    phone_number: str
    missed_call_date: str
    missed_call_time: str
    source_file: str = ""

    @property
    def missed_at(self) -> datetime:
        return datetime.strptime(
            f"{self.missed_call_date} {self.missed_call_time}",
            "%m/%d/%Y %I:%M %p",
        )

    def to_export_row(self) -> dict:
        return {
            "PhoneNumber": self.phone_number,
            "Missed Call Date": self.missed_call_date,
            "Missed Call Time": self.missed_call_time,
        }
