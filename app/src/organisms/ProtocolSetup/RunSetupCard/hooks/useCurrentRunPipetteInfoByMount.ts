import { useSelector } from 'react-redux'
import last from 'lodash/last'
import { getPipetteNameSpecs, getLabwareDefURI } from '@opentrons/shared-data'
import {
  getAttachedPipettes,
  getAttachedPipetteCalibrations,
  MATCH,
  INEXACT_MATCH,
  INCOMPATIBLE,
} from '../../../../redux/pipettes'
import { getConnectedRobotName } from '../../../../redux/robot/selectors'
import { getTipLengthCalibrations } from '../../../../redux/calibration'

import { useProtocolDetails } from '../../../RunDetails/hooks'

import type { LoadPipetteRunTimeCommand } from '@opentrons/shared-data/protocol/types/schemaV6/command/setup'
import type { PickUpTipRunTimeCommand } from '@opentrons/shared-data/protocol/types/schemaV6/command/pipetting'
import type { Mount, AttachedPipette } from '../../../../redux/pipettes/types'
import type {
  LabwareDefinition2,
  PipetteNameSpecs,
} from '@opentrons/shared-data'
import type { State } from '../../../../redux/types'

const EMPTY_MOUNTS = { left: null, right: null }

export interface PipetteInfo {
  pipetteSpecs: PipetteNameSpecs
  tipRacksForPipette: Array<{
    displayName: string
    tipRackDef: LabwareDefinition2
    lastModifiedDate: string
  }>
  requestedPipetteMatch:
    | typeof MATCH
    | typeof INEXACT_MATCH
    | typeof INCOMPATIBLE
  pipetteCalDate: string | null
}

export function useCurrentRunPipetteInfoByMount(): {
  [mount in Mount]: PipetteInfo | null
} {
  const { protocolData } = useProtocolDetails()
  const robotName = useSelector((state: State) => getConnectedRobotName(state))
  const attachedPipettes = useSelector((state: State) =>
    getAttachedPipettes(state, robotName)
  )
  const attachedPipetteCalibrations = useSelector((state: State) =>
    robotName != null
      ? getAttachedPipetteCalibrations(state, robotName)
      : EMPTY_MOUNTS
  )
  const tipLengthCalibrations = useSelector((state: State) =>
    getTipLengthCalibrations(state, robotName)
  )

  if (protocolData == null) {
    return EMPTY_MOUNTS
  }
  const { pipettes, labware, labwareDefinitions, commands } = protocolData
  const loadPipetteCommands = commands.filter(
    (command): command is LoadPipetteRunTimeCommand =>
      command.commandType === 'loadPipette'
  )
  const pickUpTipCommands = commands.filter(
    (command): command is PickUpTipRunTimeCommand =>
      command.commandType === 'pickUpTip'
  )

  return Object.entries(pipettes).reduce((acc, [pipetteId, pipette]) => {
    const loadCommand = loadPipetteCommands.find(
      command => command.result?.pipetteId === pipetteId
    )
    if (loadCommand != null) {
      const { mount } = loadCommand.params
      const requestedPipetteName = pipette.name
      const pipetteSpecs = getPipetteNameSpecs(requestedPipetteName)

      if (pipetteSpecs != null) {
        const tipRackDefs: LabwareDefinition2[] = pickUpTipCommands.reduce<
          LabwareDefinition2[]
        >((acc, command) => {
          if (pipetteId === command.params?.pipetteId) {
            const tipRack = labware[command.params?.labwareId]
            const tipRackDefinition = labwareDefinitions[tipRack.definitionId]
            if (tipRackDefinition != null && !acc.includes(tipRackDefinition)) {
              return [...acc, tipRackDefinition]
            }
          }
          return acc
        }, [])

        const attachedPipette = attachedPipettes[mount as Mount]
        const requestedPipetteMatch = getRequestedPipetteMatch(
          pipette.name,
          attachedPipette
        )

        const tipRacksForPipette = tipRackDefs.map(tipRackDef => {
          const tlcDataMatch = last(
            tipLengthCalibrations.filter(
              tlcData =>
                tlcData.uri === getLabwareDefURI(tipRackDef) &&
                attachedPipette != null &&
                tlcData.pipette === attachedPipette.id
            )
          )

          const lastModifiedDate =
            tlcDataMatch != null && requestedPipetteMatch !== INCOMPATIBLE
              ? tlcDataMatch.lastModified
              : null

          return {
            displayName: tipRackDef.metadata.displayName,
            lastModifiedDate,
            tipRackDef,
          }
        })

        const pipetteCalDate =
          requestedPipetteMatch !== INCOMPATIBLE
            ? attachedPipetteCalibrations[mount]?.offset?.lastModified
            : null
        return {
          ...acc,
          [mount]: {
            name: requestedPipetteName,
            id: pipetteId,
            pipetteSpecs,
            tipRacksForPipette,
            requestedPipetteMatch,
            pipetteCalDate,
          },
        }
      } else {
        return acc
      }
    } else {
      return acc
    }
  }, EMPTY_MOUNTS)
}

function getRequestedPipetteMatch(
  requestedPipetteName: string,
  attachedPipette: AttachedPipette | null
): string {
  if (
    attachedPipette?.modelSpecs?.backCompatNames != null &&
    attachedPipette?.modelSpecs?.backCompatNames.includes(requestedPipetteName)
  ) {
    return INEXACT_MATCH
  } else if (requestedPipetteName === attachedPipette?.modelSpecs?.name) {
    return MATCH
  } else {
    return INCOMPATIBLE
  }
}
