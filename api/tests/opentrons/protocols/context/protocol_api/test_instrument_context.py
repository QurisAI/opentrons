"""Tests for the InstrumentContext implementation core."""
from typing import cast

import pytest
from decoy import Decoy

from opentrons.types import Mount
from opentrons.hardware_control import SyncHardwareAPI
from opentrons.protocols.api_support.types import APIVersion
from opentrons.protocols.api_support.definitions import MAX_SUPPORTED_VERSION
from opentrons.protocols.context.protocol import AbstractProtocol

from opentrons.protocols.context.protocol_api.instrument_context import (
    InstrumentContextImplementation,
)


@pytest.fixture(params=[Mount.LEFT, Mount.RIGHT])
def mount(request: pytest.FixtureRequest) -> Mount:
    """Set the subject's mount."""
    return cast(Mount, request.param)  # type: ignore[attr-defined]


@pytest.fixture
def api_version() -> APIVersion:
    """Set the subject's API version."""
    return MAX_SUPPORTED_VERSION


@pytest.fixture
def mock_sync_hardware_api(
    decoy: Decoy, mount: Mount, api_version: APIVersion
) -> SyncHardwareAPI:
    """Get a mocked out HardwareControlAPI dependency."""
    hw_api = decoy.mock(name="SyncHardwareAPI")
    decoy.when(hw_api.get_attached_instrument(mount)).then_return(
        {
            "default_aspirate_flow_rates": {str(api_version): 123},
            "default_dispense_flow_rates": {str(api_version): 456},
            "default_blow_out_flow_rates": {str(api_version): 789},
        }
    )
    return cast(SyncHardwareAPI, hw_api)


@pytest.fixture
def mock_protocol_impl(
    decoy: Decoy, mock_sync_hardware_api: SyncHardwareAPI
) -> AbstractProtocol:
    protocol_impl = decoy.mock(cls=AbstractProtocol)
    decoy.when(protocol_impl.get_hardware()).then_return(mock_sync_hardware_api)
    return protocol_impl


@pytest.fixture
def subject(
    mock_protocol_impl: AbstractProtocol,
    mount: Mount,
    api_version: APIVersion,
) -> InstrumentContextImplementation:
    return InstrumentContextImplementation(
        protocol_interface=mock_protocol_impl,
        mount=mount,
        instrument_name="cool pipette",
        default_speed=1234,
        api_version=api_version,
    )


def test_home(
    mount: Mount,
    decoy: Decoy,
    mock_sync_hardware_api: SyncHardwareAPI,
    subject: InstrumentContextImplementation,
) -> None:
    """It should home the pipette's Z-axis and plunger."""
    subject.home()

    decoy.verify(
        mock_sync_hardware_api.home_z(mount=mount, allow_home_other=True),
        mock_sync_hardware_api.home_plunger(mount),
    )


@pytest.mark.parametrize("api_version", [APIVersion(2, 12)])
def test_home_legacy_behvaior(
    mount: Mount,
    decoy: Decoy,
    mock_sync_hardware_api: SyncHardwareAPI,
    subject: InstrumentContextImplementation,
) -> None:
    """It should avoid homing other instrument in API version <= 2.12."""
    subject.home()

    decoy.verify(
        mock_sync_hardware_api.home_z(mount=mount, allow_home_other=False),
        mock_sync_hardware_api.home_plunger(mount),
    )
