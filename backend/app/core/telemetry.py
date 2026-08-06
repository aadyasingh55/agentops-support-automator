from contextlib import contextmanager
from datetime import datetime
from time import perf_counter
from typing import Any, Iterator
from uuid import uuid4


class AgentTelemetry:
    """Small local trace helper with an AgentOps-compatible boundary.

    The project can run without external API keys. If the real AgentOps SDK is
    installed later, this is the single place to initialize and forward traces.
    """

    def __init__(self) -> None:
        self.trace_id = f"trace_{uuid4().hex[:12]}"

    @contextmanager
    def node(self, name: str) -> Iterator[dict[str, Any]]:
        started = perf_counter()
        event: dict[str, Any] = {
            "trace_id": self.trace_id,
            "node": name,
            "started_at": datetime.utcnow().isoformat(),
        }
        try:
            yield event
            event["status"] = "completed"
        except Exception as exc:
            event["status"] = "failed"
            event["error"] = str(exc)
            raise
        finally:
            event["duration_ms"] = round((perf_counter() - started) * 1000, 2)
