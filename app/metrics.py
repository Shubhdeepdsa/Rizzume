from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class EndpointMetrics:
    requests_total: int = 0
    errors_total: int = 0
    total_duration_seconds: float = 0.0

    def record(self, duration: float, error: bool) -> None:
        self.requests_total += 1
        if error:
            self.errors_total += 1
        self.total_duration_seconds += duration


_lock = threading.Lock()
_metrics: Dict[str, EndpointMetrics] = {}


def _get_bucket(path: str, method: str) -> EndpointMetrics:
    key = f"{method.upper()} {path}"
    with _lock:
        bucket = _metrics.get(key)
        if bucket is None:
            bucket = EndpointMetrics()
            _metrics[key] = bucket
        return bucket


def record_request(path: str, method: str, duration: float, error: bool) -> None:
    bucket = _get_bucket(path, method)
    bucket.record(duration, error)


def render_metrics_text() -> str:
    """
    Render metrics in a simple text format.
    This is intentionally minimal, but roughly Prometheus-like.
    """
    lines = []
    with _lock:
        for key, bucket in _metrics.items():
            method, path = key.split(" ", 1)
            avg_duration = (
                bucket.total_duration_seconds / bucket.requests_total
                if bucket.requests_total
                else 0.0
            )
            lines.append(
                f'requests_total{{method="{method}",path="{path}"}} {bucket.requests_total}'
            )
            lines.append(
                f'errors_total{{method="{method}",path="{path}"}} {bucket.errors_total}'
            )
            lines.append(
                "request_duration_seconds_average"
                f'{{method="{method}",path="{path}"}} {avg_duration:.6f}'
            )
    return "\n".join(lines) + "\n"

