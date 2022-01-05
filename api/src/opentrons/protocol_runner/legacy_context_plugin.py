"""Customize the ProtocolEngine to monitor and control legacy (APIv2) protocols."""
from __future__ import annotations

import asyncio
from typing import (
    Callable,
    Optional,
    NamedTuple,
)

from opentrons.commands.types import CommandMessage as LegacyCommand
from opentrons.hardware_control import HardwareControlAPI
from opentrons.hardware_control.types import PauseType as HardwarePauseType
from opentrons.protocol_engine import AbstractPlugin, actions as pe_actions

from .legacy_wrappers import (
    LegacyInstrumentLoadInfo,
    LegacyLabwareLoadInfo,
    LegacyProtocolContext,
    LegacyModuleLoadInfo,
)
from .legacy_command_mapper import LegacyCommandMapper
from .thread_async_queue import ThreadAsyncQueue, QueueClosed


class ContextUnsubscribe(NamedTuple):
    """Unsubscribe functions for broker messages."""

    command_broker: Callable[[], None]
    labware_broker: Callable[[], None]
    pipette_broker: Callable[[], None]
    module_broker: Callable[[], None]


# NOTES:
#
# Worker thread queues up actions at its leisure
#
# Shoveler task doesn't need to support cancellation
# because the queue of actions should be bounded and small at that point.
#
#
# legacy.plugin.teardown() called automatically at some point
#
# Is it okay for tearing down the plugin to be blocking?
#
# How do I get an async event loop task to block until either:
# * a single item can be retrieved from a queue.Queue (not an asyncio.Queue)
# * the queue is closed
# And sleep (yield) while blocking


# Before we close the ProtocolEngine, any scheduled actions from the
# legacy mapper must have made it in to that ProtocolEngine

# .finalize method

# TODO: Confirm that things get cleaned up when you cancel a protocol.

# TODO: Run to ground why this is hanging


class LegacyContextPlugin(AbstractPlugin):
    """A ProtocolEngine plugin wrapping a legacy ProtocolContext.

    In the legacy ProtocolContext, protocol execution is accomplished
    by direct communication with the HardwareControlAPI, as opposed to an
    intermediate layer like the ProtocolEngine. This plugin wraps up
    and hides this behavior, so the ProtocolEngine can monitor and control
    the run of a legacy protocol without affecting the execution of
    the protocol commands themselves.

    This plugin allows a ProtocolEngine to:

    1. Play/pause the protocol run using the HardwareControlAPI, as was done before
       the ProtocolEngine existed.
    2. Subscribe to what is being done with the legacy ProtocolContext,
       and insert matching commands into ProtocolEngine state for
       purely progress-tracking purposes.
    """

    def __init__(
        self,
        hardware_api: HardwareControlAPI,
        protocol_context: LegacyProtocolContext,
        legacy_command_mapper: Optional[LegacyCommandMapper] = None,
    ) -> None:
        """Initialize the plugin with its dependencies."""
        self._hardware_api = hardware_api
        self._protocol_context = protocol_context
        self._legacy_command_mapper = legacy_command_mapper or LegacyCommandMapper()
        self._unsubscribe: Optional[ContextUnsubscribe] = None

        self._actions_to_dispatch = ThreadAsyncQueue[pe_actions.Action]()
        self._action_shoveling_task: Optional[asyncio.Task[None]] = None

    def setup(self) -> None:
        """Set up the plugin.

        Called by Protocol Engine when the plugin is added to it.

        * Subscribe to the legacy context's message brokers.
        * Prepare a background task to pass legacy commands to Protocol Engine.
        """
        context = self._protocol_context

        command_unsubscribe = context.broker.subscribe(
            topic="command",
            handler=self._handle_legacy_command,
        )
        labware_unsubscribe = context.labware_load_broker.subscribe(
            callback=self._handle_labware_loaded
        )
        pipette_unsubscribe = context.instrument_load_broker.subscribe(
            callback=self._handle_instrument_loaded
        )
        module_unsubscribe = context.module_load_broker.subscribe(
            callback=self._handle_module_loaded
        )

        self._unsubscribe = ContextUnsubscribe(
            command_broker=command_unsubscribe,
            labware_broker=labware_unsubscribe,
            pipette_broker=pipette_unsubscribe,
            module_broker=module_unsubscribe,
        )

        self._action_shoveling_task = asyncio.create_task(self._shovel_all_actions())

    def teardown(self) -> None:
        """Unsubscribe from the context's message brokers.

        Called by Protocol Engine when the engine stops.
        """
        if self._unsubscribe:
            for unsubscribe in self._unsubscribe:
                unsubscribe()

        self._unsubcribe = None

    async def finalize(self) -> None:
        """Inform the plugin that the APIv2 script has exited.

        This method will wait until the plugin is finished sending commands
        into the Protocol Engine, and then return.
        You must call this method *before* stopping the Protocol Engine,
        so those commands make it in first.
        """
        # TODO: Think through whether this can be merged into teardown().
        # TODO: What if the engine is never started?
        if self._action_shoveling_task is not None:
            self._actions_to_dispatch.done_putting()
            await self._action_shoveling_task

    def handle_action(self, action: pe_actions.Action) -> None:
        """React to a ProtocolEngine action."""
        if isinstance(action, pe_actions.PlayAction):
            self._hardware_api.resume(HardwarePauseType.PAUSE)

        elif (
            isinstance(action, pe_actions.PauseAction)
            and action.source == pe_actions.PauseSource.CLIENT
        ):
            self._hardware_api.pause(HardwarePauseType.PAUSE)

    def _handle_legacy_command(self, command: LegacyCommand) -> None:
        pe_actions = self._legacy_command_mapper.map_command(command=command)
        for action in pe_actions:
            self._actions_to_dispatch.put(action)

    def _handle_labware_loaded(self, labware_load_info: LegacyLabwareLoadInfo) -> None:
        pe_command = self._legacy_command_mapper.map_labware_load(
            labware_load_info=labware_load_info
        )
        action = pe_actions.UpdateCommandAction(command=pe_command)
        self._actions_to_dispatch.put(action)

    def _handle_instrument_loaded(
        self, instrument_load_info: LegacyInstrumentLoadInfo
    ) -> None:
        pe_command = self._legacy_command_mapper.map_instrument_load(
            instrument_load_info=instrument_load_info
        )
        action = pe_actions.UpdateCommandAction(command=pe_command)
        self._actions_to_dispatch.put(action)

    def _handle_module_loaded(self, module_load_info: LegacyModuleLoadInfo) -> None:
        pe_command = self._legacy_command_mapper.map_module_load(
            module_load_info=module_load_info
        )
        action = pe_actions.UpdateCommandAction(command=pe_command)
        self._actions_to_dispatch.put(action)

    async def _shovel_all_actions(self) -> None:
        while True:
            try:
                action = await self._actions_to_dispatch.get_async()
            except QueueClosed:
                break
            else:
                self.dispatch(action)
