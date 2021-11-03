import * as React from 'react'
import { when } from 'jest-when'
import { Provider } from 'react-redux'
import { createStore, Store } from 'redux'
import { renderHook } from '@testing-library/react-hooks'
import { getPipetteNameSpecs, PipetteName } from '@opentrons/shared-data'
import { getProtocolData } from '../../../../redux/protocol'
import { getPipetteMount } from '../../utils/getPipetteMount'
import * as hooks from '../hooks'
import { getLabwareLocation } from '../../utils/getLabwareLocation'
import { getLabwarePositionCheckSteps } from '../getLabwarePositionCheckSteps'
import type { PickUpTipCommand } from '@opentrons/shared-data/protocol/types/schemaV6/command/pipetting'
import type { LoadLabwareCommand } from '@opentrons/shared-data/protocol/types/schemaV6/command/setup'

jest.mock('@opentrons/shared-data')
jest.mock('../getLabwarePositionCheckSteps')
jest.mock('../../../../redux/protocol')
jest.mock('../../utils/getPipetteMount')
jest.mock('../../utils/getLabwareLocation')

const PRIMARY_PIPETTE_ID = 'PRIMARY_PIPETTE_ID'
const PRIMARY_PIPETTE_NAME = 'PRIMARY_PIPETTE_NAME' as PipetteName
const PRIMARY_PIPETTE_NUM_CHANNELS = 8
const SECONDARY_PIPETTE_ID = 'SECONDARY_PIPETTE_ID'
const SECONDARY_PIPETTE_NAME = 'SECONDARY_PIPETTE_NAME'

const PICKUP_TIP_LABWARE_ID = 'PICKUP_TIP_LABWARE_ID'
const PICKUP_TIP_LABWARE_SLOT = '3'
const PICKUP_TIP_LABWARE_DISPLAY_NAME = 'PICKUP_TIP_LABWARE_DISPLAY_NAME'

const mockGetProtocolData = getProtocolData as jest.MockedFunction<
  typeof getProtocolData
>
const mockGetPipetteNameSpecs = getPipetteNameSpecs as jest.MockedFunction<
  typeof getPipetteNameSpecs
>
const mockGetLabwarePositionCheckSteps = getLabwarePositionCheckSteps as jest.MockedFunction<
  typeof getLabwarePositionCheckSteps
>
const mockGetPipetteMount = getPipetteMount as jest.MockedFunction<
  typeof getPipetteMount
>
const mockGetLabwareLocation = getLabwareLocation as jest.MockedFunction<
  typeof getLabwareLocation
>

const store: Store<any> = createStore(jest.fn(), {})

describe('useIntroInfo', () => {
  beforeEach(() => {
    const protocolCommands = [
      {
        commandType: 'loadLabware',
        id: '4abc123',
        params: {
          labwareId: PICKUP_TIP_LABWARE_ID,
          location: {
            slotName: PICKUP_TIP_LABWARE_SLOT,
          },
        },
      } as LoadLabwareCommand,
    ]
    mockGetLabwarePositionCheckSteps.mockReturnValue([
      {
        labwareId: PICKUP_TIP_LABWARE_ID,
        section: 'PRIMARY_PIPETTE_TIPRACKS',
        // LPC commands that are generated, different than commands that come from protocol analysis
        commands: [
          {
            commandType: 'pickUpTip',
            params: {
              pipetteId: PRIMARY_PIPETTE_ID,
              labwareId: PICKUP_TIP_LABWARE_ID,
            },
          } as PickUpTipCommand,
        ],
      },
    ])
    mockGetProtocolData.mockReturnValue({
      labware: {
        [PICKUP_TIP_LABWARE_ID]: {
          slot: PICKUP_TIP_LABWARE_SLOT,
          displayName: PICKUP_TIP_LABWARE_DISPLAY_NAME,
        },
      },
      pipettes: {
        [PRIMARY_PIPETTE_ID]: {
          name: PRIMARY_PIPETTE_NAME,
          mount: 'left',
        },
        [SECONDARY_PIPETTE_ID]: {
          name: SECONDARY_PIPETTE_NAME,
          mount: 'right',
        },
      },
      commands: protocolCommands,
    } as any)

    when(mockGetPipetteNameSpecs)
      .calledWith(PRIMARY_PIPETTE_NAME)
      .mockReturnValue({ channels: PRIMARY_PIPETTE_NUM_CHANNELS } as any)

    when(mockGetPipetteMount)
      .calledWith(PRIMARY_PIPETTE_ID, protocolCommands)
      .mockReturnValue('left')

    when(mockGetLabwareLocation)
      .calledWith(PICKUP_TIP_LABWARE_ID, protocolCommands)
      .mockReturnValue(PICKUP_TIP_LABWARE_SLOT)
  })
  it('should gather all labware position check intro screen data', () => {
    const wrapper: React.FunctionComponent<{}> = ({ children }) => (
      <Provider store={store}>{children}</Provider>
    )
    const { result } = renderHook(hooks.useIntroInfo, { wrapper })
    const {
      primaryTipRackSlot,
      primaryTipRackName,
      primaryPipetteMount,
      secondaryPipetteMount,
      numberOfTips,
      firstStepLabwareSlot,
    } = result.current as any
    expect(primaryTipRackSlot).toBe(PICKUP_TIP_LABWARE_SLOT)
    expect(primaryTipRackName).toBe(PICKUP_TIP_LABWARE_DISPLAY_NAME)
    expect(primaryPipetteMount).toBe('left')
    expect(secondaryPipetteMount).toBe('right')
    expect(numberOfTips).toBe(8)
    expect(firstStepLabwareSlot).toBe(PICKUP_TIP_LABWARE_SLOT)
  })
})
