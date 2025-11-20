import { useQuery } from '@tanstack/react-query'
import { fetchProjects } from '../api/bonita'
import type { ProjectListItem, ProjectStatus } from '../types/project'

interface UseProjectsOptions {
  statusFilter?: ProjectStatus
  ownerOnly?: boolean
}

export const useProjects = (options: UseProjectsOptions = {}) =>
  useQuery<ProjectListItem[], Error>({
    queryKey: ['projects', options.statusFilter, options.ownerOnly],
    queryFn: () => fetchProjects(options.statusFilter, options.ownerOnly),
  })
