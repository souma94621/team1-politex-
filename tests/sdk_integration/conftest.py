import pytest
import asyncio

from broker.system_bus import SystemBus

from regulator_component import RegulatorComponent


@pytest.fixture
async def sdk_runtime():

    bus = SystemBus()

    component = RegulatorComponent(
        component_id="regulator-test",
        bus=bus
    )

    await component.start()

    yield bus

    await component.stop()


async def wait_for_message(
    storage: list,
    timeout: int = 30
):

    start = asyncio.get_event_loop().time()

    while (
        not storage and
        (asyncio.get_event_loop().time() - start) < timeout
    ):
        await asyncio.sleep(0.5)

    return storage