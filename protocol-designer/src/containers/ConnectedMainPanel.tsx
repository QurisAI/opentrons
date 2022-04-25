import * as React from 'react'
import { connect } from 'react-redux'
import { Splash } from '@opentrons/components'
import { START_TERMINAL_ITEM_ID, TerminalItemId } from '../steplist'
import { Portal as MainPageModalPortal } from '../components/portals/MainPageModalPortal'
import { DeckSetupManager } from '../components/DeckSetupManager'
import { ConnectedFilePage } from '../containers/ConnectedFilePage'
import { SettingsPage } from '../components/SettingsPage'
import { LiquidsPage } from '../components/LiquidsPage'
import { GroupSpheroidsPage } from "../components/GroupSpheroidsPage"
import { Hints } from '../components/Hints'
import { LiquidPlacementModal } from '../components/LiquidPlacementModal'
import { LabwareSelectionModal } from '../components/LabwareSelectionModal'
import { FormManager } from '../components/FormManager'
import { TimelineAlerts } from '../components/alerts/TimelineAlerts'

import { getSelectedTerminalItemId } from '../ui/steps'
import { selectors as labwareIngredSelectors } from '../labware-ingred/selectors'
import { selectors, Page } from '../navigation'
import { BaseState } from '../types'

interface Props {
  page: Page
  selectedTerminalItemId: TerminalItemId | null | undefined
  ingredSelectionMode: boolean
}

function MainPanelComponent(props: Props): JSX.Element {
  const { page, selectedTerminalItemId, ingredSelectionMode } = props
  switch (page) {
    case 'file-splash':
      return <Splash />
    case 'file-detail':
      return <ConnectedFilePage />
    case 'liquids':
      return <LiquidsPage />
    case 'move-spheroid':
      return <GroupSpheroidsPage />
    case 'settings-app':
      return <SettingsPage />
    default: {
      const startTerminalItemSelected =
        selectedTerminalItemId === START_TERMINAL_ITEM_ID
      return (
        <>
          <MainPageModalPortal>
            <TimelineAlerts />
            <Hints />
            {startTerminalItemSelected && <LabwareSelectionModal />}
            <FormManager />
            {startTerminalItemSelected && ingredSelectionMode && (
              <LiquidPlacementModal />
            )}
          </MainPageModalPortal>
          <DeckSetupManager />
        </>
      )
    }
  }
}

function mapStateToProps(state: BaseState): Props {
  return {
    page: selectors.getCurrentPage(state),
    selectedTerminalItemId: getSelectedTerminalItemId(state),
    ingredSelectionMode:
      labwareIngredSelectors.getSelectedLabwareId(state) != null,
  }
}

export const ConnectedMainPanel = connect(mapStateToProps)(MainPanelComponent)
