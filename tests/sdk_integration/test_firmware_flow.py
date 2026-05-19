import pytest
import uuid
from datetime import datetime

from config import Config

from models import (
    FirmwareRequest,
    FirmwareResult
)


@pytest.mark.asyncio
async def test_firmware_certification_flow(
    sdk_runtime
):

    bus = sdk_runtime

    request_id = str(uuid.uuid4())

    received = []

    async def on_result(message):

        result = FirmwareResult(**message)

        if result.request_id == request_id:
            received.append(result)

    await bus.subscribe(
        Config.TOPIC_FIRMWARE_RESULT,
        on_result
    )

    request = FirmwareRequest(
        request_id=request_id,
        timestamp=datetime.utcnow(),
        developer_id="dev-team-01",
        firmware={
            "repository_url": "https://github.com/example/drone-fw",
            "commit_hash": "a1b2c3d4",
            "version": "2.0.1"
        },
        drone_type="quadcopter-v4"
    )

    await bus.publish(
        Config.TOPIC_FIRMWARE_REQUEST,
        request.model_dump()
    )

    import asyncio

    start = asyncio.get_event_loop().time()

    while (
        not received and
        (asyncio.get_event_loop().time() - start) < 30
    ):
        await asyncio.sleep(0.5)

    assert received

    result = received[0]

    assert result.request_id == request_id

    assert result.status in [
        "CERTIFIED",
        "REJECTED"
    ]

    if result.status == "CERTIFIED":
        assert result.certificate is not None