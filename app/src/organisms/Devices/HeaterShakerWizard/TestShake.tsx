import React from 'react'
import { Trans, useTranslation } from 'react-i18next'
import {
  useCreateCommandMutation,
  useCreateLiveCommandMutation,
} from '@opentrons/react-api-client'
import {
  ALIGN_CENTER,
  ALIGN_FLEX_START,
  COLORS,
  DIRECTION_COLUMN,
  DIRECTION_ROW,
  Flex,
  Icon,
  SIZE_AUTO,
  SPACING,
  TYPOGRAPHY,
  useHoverTooltip,
} from '@opentrons/components'
import {
  RPM,
  HS_RPM_MAX,
  HS_RPM_MIN,
  CreateCommand,
} from '@opentrons/shared-data'
import { TertiaryButton } from '../../../atoms/buttons'
import { Tooltip } from '../../../atoms/Tooltip'
import { StyledText } from '../../../atoms/text'
import { Divider } from '../../../atoms/structure'
import { InputField } from '../../../atoms/InputField'
import { Collapsible } from '../../ModuleCard/Collapsible'
import { useLatchControls } from '../../ModuleCard/hooks'
import { useModuleIdFromRun } from '../../ModuleCard/useModuleIdFromRun'
import { useRunStatuses } from '../hooks'
import { HeaterShakerModuleCard } from './HeaterShakerModuleCard'

import type { HeaterShakerModule } from '../../../redux/modules/types'
import type {
  HeaterShakerSetAndWaitForShakeSpeedCreateCommand,
  HeaterShakerDeactivateShakerCreateCommand,
  HeaterShakerCloseLatchCreateCommand,
} from '@opentrons/shared-data/protocol/types/schemaV6/command/module'
import type { ProtocolModuleInfo } from '../../Devices/ProtocolRun/utils/getProtocolModulesInfo'

interface TestShakeProps {
  module: HeaterShakerModule
  setCurrentPage: React.Dispatch<React.SetStateAction<number>>
  moduleFromProtocol?: ProtocolModuleInfo
  currentRunId?: string
}

export function TestShake(props: TestShakeProps): JSX.Element {
  const { module, setCurrentPage, moduleFromProtocol, currentRunId } = props
  const { t } = useTranslation(['heater_shaker', 'device_details'])
  const { createLiveCommand } = useCreateLiveCommandMutation()
  const { createCommand } = useCreateCommandMutation()
  const [isExpanded, setExpanded] = React.useState(false)
  const { isRunIdle, isRunTerminal } = useRunStatuses()
  const [shakeValue, setShakeValue] = React.useState<string | null>(null)
  const [targetProps, tooltipProps] = useHoverTooltip()
  const { toggleLatch, isLatchClosed } = useLatchControls(module, currentRunId)
  const { moduleIdFromRun } = useModuleIdFromRun(module, currentRunId ?? null)
  const isShaking = module.data.speedStatus !== 'idle'
  const moduleId = isRunIdle ? moduleIdFromRun : module.id

  const closeLatchCommand: HeaterShakerCloseLatchCreateCommand = {
    commandType: 'heaterShaker/closeLabwareLatch',
    params: {
      moduleId,
    },
  }

  const setShakeCommand: HeaterShakerSetAndWaitForShakeSpeedCreateCommand = {
    commandType: 'heaterShaker/setAndWaitForShakeSpeed',
    params: {
      moduleId,
      rpm: shakeValue !== null ? parseInt(shakeValue) : 0,
    },
  }

  const stopShakeCommand: HeaterShakerDeactivateShakerCreateCommand = {
    commandType: 'heaterShaker/deactivateShaker',
    params: {
      moduleId,
    },
  }

  const sendCommands = async (): Promise<void> => {
    const commands: CreateCommand[] = isShaking
      ? [stopShakeCommand]
      : [closeLatchCommand, setShakeCommand]

    for (const command of commands) {
      // await each promise to make sure the server receives requests in the right order
      if (isRunIdle && currentRunId != null) {
        await createCommand({
          runId: currentRunId,
          command,
        }).catch((e: Error) => {
          console.error(
            `error setting module status with command type ${command.commandType}: ${e.message}`
          )
        })
      } else if (isRunTerminal || currentRunId == null) {
        await createLiveCommand({
          command,
        }).catch((e: Error) => {
          console.error(
            `error setting module status with command type ${command.commandType}: ${e.message}`
          )
        })
      }
    }
    setShakeValue(null)
  }

  const errorMessage =
    shakeValue != null &&
    (parseInt(shakeValue) < HS_RPM_MIN || parseInt(shakeValue) > HS_RPM_MAX)
      ? t('device_details:input_out_of_range')
      : null

  return (
    <Flex flexDirection={DIRECTION_COLUMN}>
      <StyledText fontWeight={TYPOGRAPHY.fontWeightSemiBold}>
        {t('step_4_of_4')}
      </StyledText>
      <Flex
        marginTop={SPACING.spacing3}
        marginBottom={SPACING.spacing4}
        backgroundColor={COLORS.background}
        paddingTop={SPACING.spacing4}
        paddingLeft={SPACING.spacing4}
        flexDirection={DIRECTION_ROW}
        data-testid="test_shake_banner_info"
      >
        <Flex
          size={SPACING.spacing6}
          color={COLORS.darkGreyEnabled}
          paddingBottom={SPACING.spacing4}
        >
          <Icon name="information" aria-label="information" />
        </Flex>
        <Flex
          flexDirection={DIRECTION_COLUMN}
          paddingLeft={SPACING.spacing3}
          fontSize={TYPOGRAPHY.fontSizeP}
          paddingBottom={SPACING.spacing4}
        >
          <StyledText fontWeight={TYPOGRAPHY.fontWeightRegular}>
            <Trans
              t={t}
              i18nKey={
                moduleFromProtocol != null
                  ? 'test_shake_banner_labware_information'
                  : 'test_shake_banner_information'
              }
              values={{
                labware: moduleFromProtocol?.nestedLabwareDisplayName,
              }}
              components={{
                bold: <strong />,
                block: (
                  <StyledText
                    fontSize={TYPOGRAPHY.fontSizeH2}
                    marginBottom={SPACING.spacing5}
                  />
                ),
              }}
            />
          </StyledText>
        </Flex>
      </Flex>
      <Flex
        alignSelf={ALIGN_CENTER}
        flexDirection={DIRECTION_COLUMN}
        fontSize={TYPOGRAPHY.fontSizeCaption}
      >
        <HeaterShakerModuleCard module={module} />
        <TertiaryButton
          marginLeft={SIZE_AUTO}
          marginTop={SPACING.spacing4}
          onClick={toggleLatch}
          disabled={isShaking}
        >
          {isLatchClosed ? t('open_labware_latch') : t('close_labware_latch')}
        </TertiaryButton>

        <Flex
          flexDirection={DIRECTION_ROW}
          marginY={SPACING.spacingL}
          alignItems={ALIGN_FLEX_START}
        >
          <Flex flexDirection={DIRECTION_COLUMN} maxWidth="6.25rem">
            <StyledText
              fontSize={TYPOGRAPHY.fontSizeCaption}
              color={COLORS.darkGreyEnabled}
            >
              {t('set_shake_speed')}
            </StyledText>
            <InputField
              data-testid={`TestShake_shake_input`}
              units={RPM}
              value={shakeValue}
              onChange={e => setShakeValue(e.target.value)}
              type="number"
              caption={t('min_max_rpm', {
                min: HS_RPM_MIN,
                max: HS_RPM_MAX,
              })}
              error={errorMessage}
            />
          </Flex>
          <TertiaryButton
            fontSize={TYPOGRAPHY.fontSizeCaption}
            marginLeft={SIZE_AUTO}
            marginTop={SPACING.spacing4}
            onClick={sendCommands}
            disabled={
              !isLatchClosed ||
              (shakeValue === null && !isShaking) ||
              errorMessage != null
            }
            {...targetProps}
          >
            {isShaking ? t('stop_shaking') : t('start_shaking')}
          </TertiaryButton>
          {!isLatchClosed ? (
            <Tooltip tooltipProps={tooltipProps}>{t('cannot_shake')}</Tooltip>
          ) : null}
        </Flex>
      </Flex>
      <Divider marginY={SPACING.spacing4} />
      <Collapsible
        expanded={isExpanded}
        title={t('troubleshooting')}
        toggleExpanded={() => setExpanded(!isExpanded)}
      >
        <Flex
          flexDirection={DIRECTION_ROW}
          alignItems={ALIGN_FLEX_START}
          marginY={SPACING.spacing6}
        >
          <StyledText width="22rem">{t('troubleshoot_step_1')}</StyledText>
          <TertiaryButton
            fontSize={TYPOGRAPHY.fontSizeCaption}
            marginLeft={SIZE_AUTO}
            onClick={() => setCurrentPage(2)}
          >
            {t('go_to_step_1')}
          </TertiaryButton>
        </Flex>
        <Flex flexDirection={DIRECTION_ROW} alignItems={ALIGN_FLEX_START}>
          <StyledText width="22rem">{t('troubleshoot_step_3')}</StyledText>
          <TertiaryButton
            fontSize={TYPOGRAPHY.fontSizeCaption}
            marginLeft={SIZE_AUTO}
            onClick={() => setCurrentPage(4)}
          >
            {t('go_to_step_3')}
          </TertiaryButton>
        </Flex>
      </Collapsible>
      <Divider marginTop={SPACING.spacing4} marginBottom={SPACING.spacingXL} />
    </Flex>
  )
}
