"""Test load module command."""
from decoy import Decoy

from opentrons_shared_data.module.dev_types import ModuleDefinitionV2
from opentrons.types import DeckSlotName
from opentrons.protocol_engine.types import DeckSlotLocation, ModuleModels
from opentrons.protocol_engine.execution import (
    EquipmentHandler,
    MovementHandler,
    PipettingHandler,
    RunControlHandler,
    LoadedModuleData,
)

from opentrons.protocol_engine.commands.load_module import (
    LoadModuleParams,
    LoadModuleResult,
    LoadModuleImplementation,
)


async def test_load_module_implementation(
    decoy: Decoy,
    equipment: EquipmentHandler,
    movement: MovementHandler,
    pipetting: PipettingHandler,
    run_control: RunControlHandler,
    minimal_module_def: ModuleDefinitionV2,
) -> None:
    """A loadModule command should have an execution implementation."""
    subject = LoadModuleImplementation(
        equipment=equipment,
        movement=movement,
        pipetting=pipetting,
        run_control=run_control,
    )

    data = LoadModuleParams(
        model=ModuleModels.TEMPERATURE_MODULE_V1,
        location=DeckSlotLocation(slotName=DeckSlotName.SLOT_1),
        moduleId="some-id",
    )

    decoy.when(
        await equipment.load_module(
            model=ModuleModels.TEMPERATURE_MODULE_V1,
            location=DeckSlotLocation(slotName=DeckSlotName.SLOT_1),
            module_id="some-id",
        )
    ).then_return(
        LoadedModuleData(
            module_id="module-id",
            module_serial="mod-serial",
            definition=minimal_module_def,
        )
    )

    result = await subject.execute(data)
    assert result == LoadModuleResult(moduleId="module-id", moduleSerial="mod-serial")
