import * as React from 'react'
import { createStore, Store } from 'redux'
import { Provider } from 'react-redux'
import { QueryClient, QueryClientProvider } from 'react-query'
import { when } from 'jest-when'
import _uncastedSimpleV6Protocol from '@opentrons/shared-data/protocol/fixtures/6/simpleV6.json'
import { useLabwarePositionCheck } from '../useLabwarePositionCheck'
import { useProtocolDetails } from '../../../../RunDetails/hooks'
import { createCommand } from '@opentrons/api-client'
import { useLPCCommands } from '../useLPCCommands'
import { renderHook } from '@testing-library/react-hooks'
import { getMockLPCCommands } from '../../fixtures/commands'
import type { ProtocolFile } from '@opentrons/shared-data'
import { getLabwareLocation } from '../../../utils/getLabwareLocation'
import { getModuleLocation } from '../../../utils/getModuleLocation'

const simpleV6Protocol = (_uncastedSimpleV6Protocol as unknown) as ProtocolFile<{}>

jest.mock('@opentrons/api-client')
jest.mock('../../../../RunDetails/hooks')
jest.mock('../../../utils/getLabwareLocation')
jest.mock('../../../utils/getModuleLocation')
jest.mock('../useLPCCommands')

const mockCreateCommand = createCommand as jest.MockedFunction<
  typeof createCommand
>
const mockUseProtocolDetails = useProtocolDetails as jest.MockedFunction<
  typeof useProtocolDetails
>
const mockUseLPCCommands = useLPCCommands as jest.MockedFunction<typeof useLPCCommands>

const mockGetLabwareLocation = getLabwareLocation as jest.MockedFunction<
  typeof getLabwareLocation
>
const mockGetModuleLocation = getModuleLocation as jest.MockedFunction<
  typeof getModuleLocation
>

const store: Store<any> = createStore(jest.fn(), {})

const queryClient = new QueryClient()

const wrapper: React.FunctionComponent<{}> = ({ children }) => (
  <Provider store={store}>
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  </Provider>
)

describe('useLabwarePositionCheck', () => {
  describe('beginLPC', () => {
    beforeEach(() => {
      when(mockUseProtocolDetails).calledWith().mockReturnValue({
        protocolData: simpleV6Protocol,
        displayName: 'mock display name',
      })
      when(mockUseLPCCommands).calledWith().mockReturnValue(getMockLPCCommands())
    })
    it('should execute all prep commands', () => {
      mockCreateCommand.mockResolvedValue({
        data: { data: { id: 'some_id' } },
      } as any)
      const { result } = renderHook(useLabwarePositionCheck, { wrapper })
      const { beginLPC } = result.current as any
      beginLPC()
      
    })
  })
})
