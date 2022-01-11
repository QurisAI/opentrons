"""Tests for move groups."""
import asyncio
from typing import Iterator, Tuple

import pytest
from _pytest.fixtures import FixtureRequest
from opentrons_ot3_firmware import NodeId, ArbitrationId
from opentrons_ot3_firmware.messages.message_definitions import (
    AddLinearMoveRequest,
    GetMoveGroupRequest,
    GetMoveGroupResponse,
)
from opentrons_ot3_firmware.messages import MessageDefinition
from opentrons_ot3_firmware.messages.payloads import (
    AddLinearMoveRequestPayload,
    MoveGroupRequestPayload,
)
from opentrons_ot3_firmware.utils import UInt8Field, Int32Field, UInt32Field

from opentrons_hardware.drivers.can_bus import CanMessenger


@pytest.fixture(
    scope="session",
    params=list(range(3)),
)
def group_id(request: FixtureRequest) -> Iterator[int]:
    """A group id test fixture."""
    yield request.param  # type: ignore[attr-defined]


@pytest.mark.requires_emulator
async def test_add_moves(
    loop: asyncio.BaseEventLoop,
    can_messenger: CanMessenger,
    can_messenger_queue: "asyncio.Queue[Tuple[MessageDefinition, ArbitrationId]]",
    motor_node_id: NodeId,
    group_id: int,
) -> None:
    """It should add moves and verify that they were stored correctly."""
    durations = 100, 200, 300

    moves = (
        AddLinearMoveRequest(
            payload=AddLinearMoveRequestPayload(
                group_id=UInt8Field(group_id),
                seq_id=UInt8Field(i),
                duration=UInt32Field(duration),
                acceleration=Int32Field(0),
                velocity=Int32Field(0),
            )
        )
        for i, duration in enumerate(durations)
    )

    # Add the moves
    for move in moves:
        await can_messenger.send(node_id=motor_node_id, message=move)

    # Get the move group
    await can_messenger.send(
        node_id=motor_node_id,
        message=GetMoveGroupRequest(
            payload=MoveGroupRequestPayload(group_id=UInt8Field(group_id))
        ),
    )

    response, arbitration_id = await asyncio.wait_for(can_messenger_queue.get(), 1)

    assert isinstance(response, GetMoveGroupResponse)
    assert response.payload.num_moves.value == len(durations)
    assert response.payload.total_duration.value == sum(durations)
