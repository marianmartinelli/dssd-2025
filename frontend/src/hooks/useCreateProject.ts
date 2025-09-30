import { useMutation } from '@tanstack/react-query'
import { createProject } from '../api/bonita'
import type { ProjectFormValues, ProjectCreationResponse } from '../types/project'

export const useCreateProject = () =>
  useMutation<ProjectCreationResponse, unknown, ProjectFormValues>({
    mutationFn: createProject,
  })
