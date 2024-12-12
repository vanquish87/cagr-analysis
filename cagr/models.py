from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum


class Api(Enum):
    UPSTOX = 1
    ANGEL = 2


@dataclass
class ModVar:
    api: Api
    folder_path: str
    back_days: int
    forward_days: int
    _start: date = field(repr=False)  # Backing field for the property
    fromdate: date = field(init=False)
    todate: date = field(init=False)

    def __post_init__(self):
        self._update_dates()

    @property
    def start(self) -> date:
        return self._start

    @start.setter
    def start(self, value: date):
        self._start = value
        self._update_dates()

    # Recalculate fromdate and todate based on the current start date.
    def _update_dates(self):
        self.fromdate = self._start - timedelta(days=self.back_days)
        self.todate = self._start + timedelta(days=self.forward_days)
