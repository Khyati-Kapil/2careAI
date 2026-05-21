from __future__ import annotations

import time
from contextlib import contextmanager


class LatencyTracker:
    def __init__(self) -> None:
        self.data: dict[str, float] = {}

    @contextmanager
    def span(self, name: str):
        start = time.perf_counter()
        try:
            yield
        finally:
            self.data[name] = round((time.perf_counter() - start) * 1000, 2)

    def total(self) -> float:
        return round(sum(self.data.values()), 2)
