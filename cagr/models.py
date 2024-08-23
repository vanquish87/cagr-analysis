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
    start: date
    back_days: int
    forward_days: int
    fromdate: date = field(init=False)
    todate: date = field(init=False)

    def __post_init__(self):
        self.fromdate = self.start - timedelta(days=self.back_days)
        self.todate = self.start + timedelta(days=self.forward_days)
