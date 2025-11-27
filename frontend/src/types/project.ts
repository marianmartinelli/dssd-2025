import type { ProjectSchema } from '../lib/validation'

export type ProjectFormValues = ProjectSchema
export type WorkPlanStageForm = ProjectFormValues['workPlanStages'][number]
export type SupportType = WorkPlanStageForm['supportType']
export type PriorityLevel = ProjectFormValues['priorityLevel']

export interface ProjectCreationResponse {
  caseId: number
  processDefinitionId: string
  createdAt: string
}

export type ProjectStatus = 'in_progress' | 'completed' | 'requesting_support'

export interface WorkPlanStageResponse {
  id: number
  projectId: number
  stageName: string
  stageStart?: string
  stageEnd?: string
  supportType?: string
  description?: string
  estimatedAmount?: number
  amountCurrency?: string
  isCompleted?: boolean
}

export interface ObservationResponse {
  id: number
  projectId: number
  title: string
  description?: string
  createdDate?: string
  createdBy: string
  isResolved?: boolean
}

export interface ObservationCreate {
  projectId: number
  title: string
  description?: string
}

export interface CollaborationRequestResponse {
  id: number
  stageId: number
  work_plan_stage_id?: number
  title: string
  description?: string
  requestedAmount?: number
  amountCurrency?: string
  requestedDate?: string
  isApproved?: boolean
  isCompleted?: boolean
  committedBy: string
  committedByOrganization?: string
}

export interface ProjectListItem {
  id: number
  projectName: string
  projectDescription?: string
  projectCategory?: string
  requestingOrganization?: string
  contactEmail?: string
  contactPhone?: string
  estimatedBudget?: number
  currency?: string
  startDate?: string
  endDate?: string
  priorityLevel?: string
  supportingDocsUrl?: string
  submissionTimestamp?: string
  initiatorUserId?: string
  caseId?: number
  organizationId?: number
  status: ProjectStatus
  workPlanStages: WorkPlanStageResponse[]
  observations?: ObservationResponse[]
}

export interface ProjectsFilters {
  status?: ProjectStatus
  ownerOnly?: boolean
}

export interface CurrentUserResponse {
  username: string
  email?: string
  organizationName?: string
}

export interface SetUserOrganizationRequest {
  organizationId: number
}

export interface CollaborationCreatePayload {
  projectId: number
  stageId: number
  title: string
  description?: string
  requestedAmount?: number
  amountCurrency?: string
}

export interface StageCoverageInfo {
  stageId: number
  stageName: string
  hasApprovedCollaboration: boolean
  approvedCount: number
  totalCount: number
}

export interface ProjectTransitionReadinessResponse {
  projectId: number
  currentStatus: string
  totalStages: number
  coveredStages: number
  uncoveredStages: number
  stagesCoverage: StageCoverageInfo[]
}

export interface ProjectStartTransitionResponse {
  projectId: number
  previousStatus: string
  newStatus: string
  totalStages: number
  coveredStages: number
  uncoveredStages: number
  stagesCoverage: StageCoverageInfo[]
}
