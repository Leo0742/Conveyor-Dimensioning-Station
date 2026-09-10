"""WMS message contract and local append-only JSONL outbox."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from conveyor_dimensioning.types import DimensionResult, MeasurementStatus


class WMSMessage(BaseModel):
    """Warehouse message with a deterministic idempotency key."""

    model_config = ConfigDict(frozen=True)

    measurement_id: str
    item_id: str = Field(min_length=1)
    timestamp: datetime
    length_mm: float | None = Field(default=None, ge=0)
    width_mm: float | None = Field(default=None, ge=0)
    height_mm: float | None = Field(default=None, ge=0)
    confidence: float = Field(
        ge=0, le=1, description="Uncalibrated heuristic quality score"
    )
    measurement_status: MeasurementStatus

    @field_serializer("timestamp")
    def serialize_timestamp(self, value: datetime) -> str:
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")

    @classmethod
    def from_result(
        cls,
        item_id: str,
        result: DimensionResult,
        *,
        timestamp: datetime | None = None,
    ) -> WMSMessage:
        captured_at = timestamp or datetime.now(UTC)
        captured_at = captured_at.astimezone(UTC)
        stable_key = f"{item_id}|{captured_at.isoformat()}"
        measurement_id = str(uuid.uuid5(uuid.NAMESPACE_URL, stable_key))
        dimensions = (
            (result.length_mm, result.width_mm, result.height_mm)
            if result.status == "ok"
            else (None, None, None)
        )
        return cls(
            measurement_id=measurement_id,
            item_id=item_id,
            timestamp=captured_at,
            length_mm=dimensions[0],
            width_mm=dimensions[1],
            height_mm=dimensions[2],
            confidence=result.confidence,
            measurement_status=result.status,
        )


class JsonOutbox:
    """Append-only fallback queue for unavailable WMS transport."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def enqueue(self, message: WMSMessage) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(message.model_dump_json() + "\n")

    def pending_count(self) -> int:
        if not self.path.exists():
            return 0
        with self.path.open(encoding="utf-8") as stream:
            return sum(1 for line in stream if line.strip())
