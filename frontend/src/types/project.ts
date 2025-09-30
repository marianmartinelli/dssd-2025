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
