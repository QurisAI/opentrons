"""Test Echo firmware."""
import pytest
from opentrons_hardware.drivers.can_bus.abstract_driver import AbstractCanDriver
from opentrons_hardware.drivers.can_bus import CanMessage
from opentrons_ot3_firmware.arbitration_id import ArbitrationId


@pytest.mark.requires_emulator
async def test_send(driver: AbstractCanDriver) -> None:
    """Verify sending a message to the emulator."""
    message = CanMessage(
        arbitration_id=ArbitrationId(id=0x1FFFFFFF), data=bytearray([1, 2, 3, 4])
    )
    await driver.send(message)
