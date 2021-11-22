"""Test equipment command execution side effects."""
import pytest
from datetime import datetime
from decoy import Decoy, matchers
from opentrons.calibration_storage.helpers import uri_from_details
from opentrons_shared_data.module.dev_types import ModuleDefinitionV2

from opentrons.types import Mount as HwMount, MountType, DeckSlotName
from opentrons.hardware_control import API as HardwareAPI
from opentrons.hardware_control.modules.types import ModuleType, TemperatureModuleModel

from opentrons.protocols.models import LabwareDefinition

from opentrons.protocol_engine import errors
from opentrons.protocol_engine.errors import LabwareDefinitionDoesNotExistError
from opentrons.protocol_engine.types import (
    DeckSlotLocation,
    PipetteName,
    LoadedPipette,
    LabwareOffset,
    LabwareOffsetVector,
    ModuleModels,
)

from opentrons.protocol_engine.state import StateStore
from opentrons.protocol_engine.resources import (
    ModelUtils,
    LabwareDataProvider,
    ModuleDataProvider,
)
from opentrons.protocol_engine.execution.equipment import (
    EquipmentHandler,
    LoadedLabwareData,
    LoadedPipetteData,
)


@pytest.fixture
def state_store(decoy: Decoy) -> StateStore:
    """Get a mocked out StateStore instance."""
    return decoy.mock(cls=StateStore)


@pytest.fixture
def hardware_api(decoy: Decoy) -> HardwareAPI:
    """Get a mocked out HardwareAPI instance."""
    return decoy.mock(cls=HardwareAPI)


@pytest.fixture
def model_utils(decoy: Decoy) -> ModelUtils:
    """Get a mocked out ModelUtils instance."""
    return decoy.mock(cls=ModelUtils)


@pytest.fixture
def labware_data_provider(decoy: Decoy) -> LabwareDataProvider:
    """Get a mocked out LabwareDataProvider instance."""
    return decoy.mock(cls=LabwareDataProvider)


@pytest.fixture
def module_data_provider(decoy: Decoy) -> ModuleDataProvider:
    """Get a mocked out ModuleDataProvider instance."""
    return decoy.mock(cls=ModuleDataProvider)


@pytest.fixture
def subject(
    hardware_api: HardwareAPI,
    state_store: StateStore,
    labware_data_provider: LabwareDataProvider,
    model_utils: ModelUtils,
) -> EquipmentHandler:
    """Get an EquipmentHandler test subject with its dependencies mocked out."""
    return EquipmentHandler(
        hardware_api=hardware_api,
        state_store=state_store,
        labware_data_provider=labware_data_provider,
        model_utils=model_utils,
    )


async def test_load_labware(
    decoy: Decoy,
    model_utils: ModelUtils,
    state_store: StateStore,
    labware_data_provider: LabwareDataProvider,
    minimal_labware_def: LabwareDefinition,
    subject: EquipmentHandler,
) -> None:
    """It should load labware definition and offset data and generate an ID."""
    decoy.when(model_utils.generate_id()).then_return("unique-id")

    decoy.when(state_store.labware.get_definition_by_uri(matchers.IsA(str))).then_raise(
        LabwareDefinitionDoesNotExistError("oh no")
    )

    decoy.when(
        await labware_data_provider.get_labware_definition(
            load_name="load-name",
            namespace="opentrons-test",
            version=1,
        )
    ).then_return(minimal_labware_def)

    decoy.when(
        state_store.labware.find_applicable_labware_offset(
            definition_uri="opentrons-test/load-name/1",
            location=DeckSlotLocation(slotName=DeckSlotName.SLOT_3),
        )
    ).then_return(
        LabwareOffset(
            id="labware-offset-id",
            createdAt=datetime(year=2021, month=1, day=2),
            definitionUri="opentrons-test/load-name/1",
            location=DeckSlotLocation(slotName=DeckSlotName.SLOT_3),
            vector=LabwareOffsetVector(x=1, y=2, z=3),
        )
    )

    result = await subject.load_labware(
        location=DeckSlotLocation(slotName=DeckSlotName.SLOT_3),
        load_name="load-name",
        namespace="opentrons-test",
        version=1,
        labware_id=None,
    )

    assert result == LoadedLabwareData(
        labware_id="unique-id",
        definition=minimal_labware_def,
        offsetId="labware-offset-id",
    )


async def test_load_labware_uses_provided_id(
    decoy: Decoy,
    model_utils: ModelUtils,
    state_store: StateStore,
    labware_data_provider: LabwareDataProvider,
    minimal_labware_def: LabwareDefinition,
    subject: EquipmentHandler,
) -> None:
    """It should use the provided ID rather than generating an ID for the labware."""
    decoy.when(state_store.labware.get_definition_by_uri(matchers.IsA(str))).then_raise(
        LabwareDefinitionDoesNotExistError("oh no")
    )

    decoy.when(
        await labware_data_provider.get_labware_definition(
            load_name="load-name",
            namespace="opentrons-test",
            version=1,
        )
    ).then_return(minimal_labware_def)

    decoy.when(
        state_store.labware.find_applicable_labware_offset(
            definition_uri="opentrons-test/load-name/1",
            location=DeckSlotLocation(slotName=DeckSlotName.SLOT_3),
        )
    ).then_return(None)

    result = await subject.load_labware(
        location=DeckSlotLocation(slotName=DeckSlotName.SLOT_3),
        load_name="load-name",
        namespace="opentrons-test",
        version=1,
        labware_id="my-labware-id",
    )

    assert result == LoadedLabwareData(
        labware_id="my-labware-id", definition=minimal_labware_def, offsetId=None
    )


async def test_load_labware_uses_loaded_labware_def(
    decoy: Decoy,
    model_utils: ModelUtils,
    state_store: StateStore,
    labware_data_provider: LabwareDataProvider,
    minimal_labware_def: LabwareDefinition,
    subject: EquipmentHandler,
) -> None:
    """Loading labware should use the labware definition already in state."""
    expected_uri = uri_from_details(
        load_name="load-name",
        namespace="opentrons-test",
        version=1,
    )

    decoy.when(model_utils.generate_id()).then_return("unique-id")

    decoy.when(state_store.labware.get_definition_by_uri(expected_uri)).then_return(
        minimal_labware_def
    )

    decoy.when(
        state_store.labware.find_applicable_labware_offset(
            definition_uri="opentrons-test/load-name/1",
            location=DeckSlotLocation(slotName=DeckSlotName.SLOT_3),
        )
    ).then_return(None)

    result = await subject.load_labware(
        location=DeckSlotLocation(slotName=DeckSlotName.SLOT_3),
        load_name="load-name",
        namespace="opentrons-test",
        version=1,
        labware_id=None,
    )

    assert result == LoadedLabwareData(
        labware_id="unique-id",
        definition=minimal_labware_def,
        offsetId=None,
    )

    decoy.verify(
        await labware_data_provider.get_labware_definition(
            load_name="load-name",
            namespace="opentrons-test",
            version=1,
        ),
        times=0,
    )


async def test_load_pipette(
    decoy: Decoy,
    model_utils: ModelUtils,
    hardware_api: HardwareAPI,
    subject: EquipmentHandler,
) -> None:
    """It should load pipette data, check attachment, and generate an ID."""
    decoy.when(model_utils.generate_id()).then_return("unique-id")

    result = await subject.load_pipette(
        pipette_name=PipetteName.P300_SINGLE,
        mount=MountType.LEFT,
        pipette_id=None,
    )

    assert result == LoadedPipetteData(pipette_id="unique-id")
    decoy.verify(
        await hardware_api.cache_instruments(
            {HwMount.LEFT: PipetteName.P300_SINGLE}  # type: ignore[dict-item]
        )
    )


async def test_load_pipette_uses_provided_id(subject: EquipmentHandler) -> None:
    """It should use the provided ID rather than generating an ID for the pipette."""
    result = await subject.load_pipette(
        pipette_name=PipetteName.P300_SINGLE,
        mount=MountType.LEFT,
        pipette_id="my-pipette-id",
    )

    assert result == LoadedPipetteData(pipette_id="my-pipette-id")


async def test_load_pipette_checks_existence_with_already_loaded(
    decoy: Decoy,
    model_utils: ModelUtils,
    state_store: StateStore,
    hardware_api: HardwareAPI,
    subject: EquipmentHandler,
) -> None:
    """Loading a pipette should cache with pipettes already attached."""
    decoy.when(model_utils.generate_id()).then_return("unique-id")

    decoy.when(state_store.pipettes.get_by_mount(MountType.RIGHT)).then_return(
        LoadedPipette(
            id="pipette-id",
            mount=MountType.RIGHT,
            pipetteName=PipetteName.P300_MULTI_GEN2,
        )
    )

    result = await subject.load_pipette(
        pipette_name=PipetteName.P300_SINGLE,
        mount=MountType.LEFT,
        pipette_id=None,
    )

    assert result == LoadedPipetteData(pipette_id="unique-id")
    decoy.verify(
        await hardware_api.cache_instruments(
            {
                HwMount.LEFT: PipetteName.P300_SINGLE,  # type: ignore[dict-item]
                HwMount.RIGHT: PipetteName.P300_MULTI_GEN2,  # type: ignore[dict-item]
            }
        )
    )


async def test_load_pipette_raises_if_pipette_not_attached(
    decoy: Decoy,
    model_utils: ModelUtils,
    hardware_api: HardwareAPI,
    subject: EquipmentHandler,
) -> None:
    """Loading a pipette should should raise if unable to cache instruments."""
    decoy.when(model_utils.generate_id()).then_return("unique-id")

    decoy.when(
        await hardware_api.cache_instruments(
            {HwMount.LEFT: PipetteName.P300_SINGLE}  # type: ignore[dict-item]
        )
    ).then_raise(
        RuntimeError(
            "mount LEFT: instrument p300_single was requested, "
            "but no instrument is present"
        )
    )

    with pytest.raises(
        errors.FailedToLoadPipetteError, match=".+p300_single was requested"
    ):
        await subject.load_pipette(
            pipette_name=PipetteName.P300_SINGLE,
            mount=MountType.LEFT,
            pipette_id=None,
        )


@pytest.mark.xfail(strict=True, raises=AssertionError)
async def test_load_module(
    decoy: Decoy,
    model_utils: ModelUtils,
    state_store: StateStore,
    module_data_provider: ModuleDataProvider,
    minimal_module_def: ModuleDefinitionV2,
    subject: EquipmentHandler,
    hardware_api: HardwareAPI,
) -> None:
    """It should load labware definition and offset data and generate an ID."""
    decoy.when(model_utils.generate_id()).then_return("unique-id")

    decoy.when(
        await module_data_provider.get_module_definition(
            model=ModuleModels.TEMPERATURE_MODULE_V1
        )
    ).then_return(minimal_module_def)

    decoy.when(
        await hardware_api.find_modules(
            TemperatureModuleModel.TEMPERATURE_V1,
            ModuleType.TEMPERATURE,
        )
    ).then_return(([], None))

    await subject.load_module(
        model=ModuleModels.TEMPERATURE_MODULE_V1,
        location=DeckSlotLocation(slotName=DeckSlotName.SLOT_1),
        module_id=None,
    )
