import json
from datetime import UTC, datetime

import pytest

from conveyor_dimensioning.types import DimensionResult
from conveyor_dimensioning.wms import JsonOutbox, WMSMessage


def test_wms_message_serializes_stable_schema_and_id() -> None:
    result = DimensionResult(
        length_mm=200.2,
        width_mm=99.8,
        height_mm=10.1,
        confidence=0.93,
        status="ok",
        point_count=500,
    )
    timestamp = datetime(2026, 9, 9, 12, 0, tzinfo=UTC)

    first = WMSMessage.from_result("sku-42", result, timestamp=timestamp)
    second = WMSMessage.from_result("sku-42", result, timestamp=timestamp)
    payload = json.loads(first.model_dump_json())

    assert first.measurement_id == second.measurement_id
    assert payload == {
        "measurement_id": first.measurement_id,
        "item_id": "sku-42",
        "timestamp": "2026-09-09T12:00:00Z",
        "length_mm": 200.2,
        "width_mm": 99.8,
        "height_mm": 10.1,
        "confidence": 0.93,
        "measurement_status": "ok",
    }


def test_json_outbox_writes_one_valid_message_per_line(tmp_path) -> None:
    result = DimensionResult(
        length_mm=40,
        width_mm=30,
        height_mm=20,
        confidence=0.8,
        status="ok",
        point_count=100,
    )
    message = WMSMessage.from_result(
        "box-1", result, timestamp=datetime(2026, 9, 9, tzinfo=UTC)
    )
    outbox = JsonOutbox(tmp_path / "pending.jsonl")

    outbox.enqueue(message)

    assert outbox.pending_count() == 1
    assert json.loads((tmp_path / "pending.jsonl").read_text()) == json.loads(
        message.model_dump_json()
    )


@pytest.mark.parametrize(
    "status",
    [
        "low_confidence",
        "object_overlap",
        "insufficient_depth_data",
        "measurement_out_of_range",
    ],
)
def test_wms_message_nulls_dimensions_for_non_ok_status(status: str) -> None:
    result = DimensionResult(
        length_mm=200.2,
        width_mm=99.8,
        height_mm=10.1,
        confidence=0.7,
        status=status,
        point_count=500,
    )

    payload = WMSMessage.from_result(
        "sku-reject", result, timestamp=datetime(2026, 9, 10, tzinfo=UTC)
    ).model_dump()

    assert payload["length_mm"] is None
    assert payload["width_mm"] is None
    assert payload["height_mm"] is None
