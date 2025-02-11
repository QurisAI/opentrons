import { ModuleType } from '@opentrons/shared-data'

import type { ModuleModel } from '@opentrons/shared-data'

interface PhysicalPort {
  path: string | null
  port: number | null
  hub: number | null
}

export interface ApiBaseModule {
  id: string
  serialNumber: string
  hardwareRevision: string
  moduleModel: ModuleModel
  moduleType: ModuleType
  firmwareVersion: string
  hasAvailableUpdate: boolean
  usbPort: PhysicalPort
}

export interface TemperatureData {
  currentTemperature: number
  targetTemperature: number | null
  status: TemperatureStatus
}

export interface MagneticData {
  engaged: boolean
  height: number
  status: MagneticStatus
}

export interface ThermocyclerData {
  // TODO(mc, 2019-12-12): in_between comes from the thermocycler firmware and
  // will be rare in normal operation due to limitations in current revision
  lidStatus: 'open' | 'closed' | 'in_between'
  lidTargetTemperature: number | null
  lidTemperature: number | null
  currentTemperature: number | null
  targetTemperature: number | null
  holdTime: number | null
  rampRate: number | null
  totalStepCount: number | null
  currentStepIndex: number | null
  totalCycleCount: number | null
  currentCycleIndex: number | null
  status: ThermocyclerStatus
}
export interface HeaterShakerData {
  labwareLatchStatus: LatchStatus
  speedStatus: SpeedStatus
  temperatureStatus: TemperatureStatus
  currentSpeed: number | null
  currentTemperature: number | null
  targetSpeed: number | null
  targetTemperature: number | null
  errorDetails: string | null
  status: HeaterShakerStatus
}

export type TemperatureStatus =
  | 'idle'
  | 'holding at target'
  | 'cooling'
  | 'heating'

export type ThermocyclerStatus =
  | 'idle'
  | 'holding at target'
  | 'cooling'
  | 'heating'
  | 'error'

export type MagneticStatus = 'engaged' | 'disengaged'

export type HeaterShakerStatus = 'idle' | 'running' | 'error'

export type SpeedStatus =
  | 'holding at target'
  | 'speeding up'
  | 'slowing down'
  | 'idle'
  | 'error'

export type LatchStatus =
  | 'opening'
  | 'idle_open'
  | 'closing'
  | 'idle_closed'
  | 'idle_unknown'
  | 'unknown'
