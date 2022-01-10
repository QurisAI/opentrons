import {
  RunData,
  RUN_STATUS_STOPPED,
  RUN_STATUS_SUCCEEDED,
  RUN_ACTION_TYPE_PLAY,
  RUN_ACTION_TYPE_PAUSE,
  RUN_ACTION_TYPE_STOP,
} from '@opentrons/api-client'

import {
  getRunDisplayStatus,
  RUN_DISPLAY_STATUS_CANCELED,
  RUN_DISPLAY_STATUS_COMPLETE,
  RUN_DISPLAY_STATUS_NOT_STARTED,
} from '../getRunDisplayStatus'

const mockCompletedRun: RunData = {
  id: '1',
  createdAt: '2021-10-07T18:44:49.366581+00:00',
  status: RUN_STATUS_SUCCEEDED,
  protocolId: '1',
  actions: [
    {
      id: '1',
      createdAt: '2021-10-25T12:54:53.366581+00:00',
      actionType: RUN_ACTION_TYPE_PLAY,
    },
    {
      id: '2',
      createdAt: '2021-10-25T13:23:31.366581+00:00',
      actionType: RUN_ACTION_TYPE_PAUSE,
    },
    {
      id: '3',
      createdAt: '2021-10-25T13:26:42.366581+00:00',
      actionType: RUN_ACTION_TYPE_STOP,
    },
  ],
  commands: [{ id: '1', commandType: 'custom', status: 'succeeded' }] as any,
  errors: [],
  pipettes: [],
  labware: [],
}

const mockNotStartedRun: RunData = {
  id: '1',
  createdAt: '2021-10-07T18:44:49.366581+00:00',
  status: RUN_STATUS_STOPPED,
  protocolId: '1',
  actions: [
    {
      id: '1',
      createdAt: '2021-10-25T12:54:53.366581+00:00',
      actionType: RUN_ACTION_TYPE_STOP,
    },
  ],
  commands: [],
  errors: [],
  pipettes: [],
  labware: [],
}

const mockCanceledRun: RunData = {
  id: '1',
  createdAt: '2021-10-07T18:44:49.366581+00:00',
  status: RUN_STATUS_STOPPED,
  protocolId: '1',
  actions: [
    {
      id: '1',
      createdAt: '2021-10-25T12:54:53.366581+00:00',
      actionType: RUN_ACTION_TYPE_PLAY,
    },
    {
      id: '2',
      createdAt: '2021-10-25T13:23:31.366581+00:00',
      actionType: RUN_ACTION_TYPE_PAUSE,
    },
    {
      id: '3',
      createdAt: '2021-10-25T13:26:42.366581+00:00',
      actionType: RUN_ACTION_TYPE_STOP,
    },
  ],
  commands: [{ id: '1', commandType: 'custom', status: 'succeeded' }] as any,
  errors: [],
  pipettes: [],
  labware: [],
}

describe('getRunDisplayStatus', () => {
  it('should return a COMPLETE status is a recent run was completed', () => {
    expect(getRunDisplayStatus(mockCompletedRun)).toBe(
      RUN_DISPLAY_STATUS_COMPLETE
    )
  })
  it('should return a NOT STARTED status if a recent run was closed before starting', () => {
    expect(getRunDisplayStatus(mockNotStartedRun)).toBe(
      RUN_DISPLAY_STATUS_NOT_STARTED
    )
  })
  it('should return a CANCELED status if a recent run was canceled', () => {
    expect(getRunDisplayStatus(mockCanceledRun)).toBe(
      RUN_DISPLAY_STATUS_CANCELED
    )
  })
})
