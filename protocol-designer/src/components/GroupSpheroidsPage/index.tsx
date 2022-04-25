import * as React from 'react'
import { connect } from 'react-redux'

import { BaseState } from '../../types'
import { selectors, Page } from '../../navigation'

// import Workspace from '../../../../../quris/frontend/spheroid_grouping/src/Workspace'

interface Props {
  currentPage: Page
}

const STP = (state: BaseState): Props => ({
  currentPage: selectors.getCurrentPage(state),
})

const GroupSpheroidsPageComponent = (props: Props): JSX.Element => {
  return <>GroupSpheroid Workspace</> // <Workspace />
}
export const GroupSpheroidsPage = connect(STP)(GroupSpheroidsPageComponent)