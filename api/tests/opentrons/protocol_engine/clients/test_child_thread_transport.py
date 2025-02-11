"""Tests for am ChildThreadTransport."""

import pytest
from asyncio import get_running_loop
from datetime import datetime
from decoy import Decoy
from functools import partial


from opentrons.protocol_engine import ProtocolEngine, commands
from opentrons.protocol_engine.errors import ErrorOccurrence, ProtocolEngineError
from opentrons.protocol_engine.clients.transports import ChildThreadTransport


@pytest.fixture
async def engine(decoy: Decoy) -> ProtocolEngine:
    """Get a stubbed out ProtocolEngine."""
    return decoy.mock(cls=ProtocolEngine)


@pytest.fixture
async def subject(
    engine: ProtocolEngine,
) -> ChildThreadTransport:
    """Get a ChildThreadTransport test subject."""
    return ChildThreadTransport(engine=engine, loop=get_running_loop())


async def test_execute_command(
    decoy: Decoy,
    engine: ProtocolEngine,
    subject: ChildThreadTransport,
) -> None:
    """It should execute a command synchronously in a child thread."""
    cmd_data = commands.MoveToWellParams(
        pipetteId="pipette-id",
        labwareId="labware-id",
        wellName="A1",
    )
    cmd_result = commands.MoveToWellResult()
    cmd_request = commands.MoveToWellCreate(params=cmd_data)

    decoy.when(await engine.add_and_execute_command(request=cmd_request)).then_return(
        commands.MoveToWell(
            id="cmd-id",
            key="cmd-key",
            status=commands.CommandStatus.SUCCEEDED,
            params=cmd_data,
            result=cmd_result,
            createdAt=datetime.now(),
        )
    )

    task = partial(subject.execute_command, request=cmd_request)
    result = await get_running_loop().run_in_executor(None, task)

    assert result == cmd_result


async def test_execute_command_failure(
    decoy: Decoy,
    engine: ProtocolEngine,
    subject: ChildThreadTransport,
) -> None:
    """It should execute a load labware command."""
    cmd_data = commands.MoveToWellParams(
        pipetteId="pipette-id",
        labwareId="labware-id",
        wellName="A1",
    )
    cmd_request = commands.MoveToWellCreate(params=cmd_data)
    error = ErrorOccurrence(
        id="error-id",
        errorType="PrettyBadError",
        createdAt=datetime(year=2021, month=1, day=1),
        detail="Things are not looking good.",
    )

    decoy.when(await engine.add_and_execute_command(request=cmd_request)).then_return(
        commands.MoveToWell(
            id="cmd-id",
            key="cmd-key",
            params=cmd_data,
            status=commands.CommandStatus.FAILED,
            error=error,
            createdAt=datetime.now(),
        )
    )

    task = partial(subject.execute_command, request=cmd_request)

    with pytest.raises(ProtocolEngineError, match="Things are not looking good"):
        await get_running_loop().run_in_executor(None, task)
