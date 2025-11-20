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
}

export interface ProjectsFilters {
  status?: ProjectStatus
  ownerOnly?: boolean
}
