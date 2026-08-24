"""Period and on-disk layout of raw and staging files."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

# pipeline/src/northsource_pipeline/paths.py -> repo root is parents[3]
DEFAULT_ROOT = Path(os.environ.get("NORTHSOURCE_DATA_DIR", Path(__file__).resolve().parents[3] / "data"))

_PERIOD_RE = re.compile(r"(\d{4})-(\d{2})")


@dataclass(frozen=True)
class Period:
    year: int
    month: int

    @classmethod
    def parse(cls, text: str) -> Period:
        m = _PERIOD_RE.fullmatch(text)
        if not m:
            raise ValueError(f"period must be YYYY-MM, got {text!r}")
        year, month = int(m.group(1)), int(m.group(2))
        if not 1 <= month <= 12:
            raise ValueError(f"month out of range in {text!r}")
        return cls(year, month)

    @property
    def previous_year(self) -> int:
        return self.year - 1

    def __str__(self) -> str:
        return f"{self.year}-{self.month:02d}"


@dataclass(frozen=True)
class Layout:
    root: Path
    period: Period

    def raw(self, source: str) -> Path:
        p = self.root / "raw" / source / str(self.period)
        p.mkdir(parents=True, exist_ok=True)
        return p

    def staging(self) -> Path:
        p = self.root / "staging" / str(self.period)
        p.mkdir(parents=True, exist_ok=True)
        return p
