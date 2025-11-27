import axios from 'axios'
import type {
  ProjectFormValues,
  ProjectCreationResponse,
  ProjectListItem,
  ProjectStatus,
  CollaborationCreatePayload,
  CollaborationRequestResponse,
  CurrentUserResponse,
  ProjectStartTransitionResponse,
  ProjectTransitionReadinessResponse,
} from '../types/project'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('projectplanning_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export const login = async (username: string, password: string): Promise<{ role: string; username: string }> => {
  const { data } = await api.post<{ access_token: string; role?: string }>('/auth/login', { username, password })
  localStorage.setItem('projectplanning_token', data.access_token)
  const role = data.role || 'User'
  return { role, username }
}

export const createProject = async (payload: ProjectFormValues): Promise<ProjectCreationResponse> => {
  const { data } = await api.post<ProjectCreationResponse>('/projects', payload)
  return data
}

export const fetchProjects = async (
  statusFilter?: ProjectStatus,
  ownerOnly?: boolean
): Promise<ProjectListItem[]> => {
  const params = new URLSearchParams()

  if (statusFilter) {
    params.append('status_filter', statusFilter)
  }

  if (ownerOnly !== undefined) {
    params.append('owner_only', String(ownerOnly))
  }

  const queryString = params.toString()
  const url = `/projects${queryString ? `?${queryString}` : ''}`

  const { data } = await api.get<ProjectListItem[]>(url)
  return data
}

export const fetchProjectById = async (projectId: number): Promise<ProjectListItem> => {
  const { data } = await api.get<ProjectListItem>(`/projects/${projectId}`)
  return data
}

export const createObservation = async (observation: { projectId: number; title: string; description?: string }) => {
  const { data } = await api.post('/projects/observations', observation)
  return data
}

export const resolveObservation = async (observationId: number) => {
  const { data } = await api.post(`/projects/observations/${observationId}/resolve`)
  return data
}

export const fetchCollaborationRequests = async (projectId: number) => {
  const { data } = await api.get(`/projects/${projectId}/collaborations`)
  return data
}

export const approveCollaboration = async (collaborationId: number) => {
  const { data } = await api.put(`/projects/collaborations/${collaborationId}/commit`)
  return data
}

export const completeCollaboration = async (collaborationId: number) => {
  const { data } = await api.put(`/projects/collaborations/${collaborationId}/complete`)
  return data
}

export const completeStage = async (stageId: number) => {
  const { data } = await api.put(`/projects/stages/${stageId}/complete`)
  return data
}

export const completeProject = async (projectId: number) => {
  const { data } = await api.put(`/projects/${projectId}/complete`)
  return data
}

export const fetchCurrentUser = async (): Promise<CurrentUserResponse> => {
  const { data } = await api.get<CurrentUserResponse>('/auth/me')
  return data
}

export const setUserOrganization = async (
  organizationId: number
): Promise<void> => {
  await api.post('/auth/user/organization', { organizationId })
}

export const createCollaboration = async (
  payload: CollaborationCreatePayload
): Promise<CollaborationRequestResponse> => {
  const { data } = await api.post<CollaborationRequestResponse>(
    '/projects/collaborations',
    payload
  )
  return data
}

export const checkProjectTransitionReadiness = async (
  projectId: number
): Promise<ProjectTransitionReadinessResponse> => {
  const { data } = await api.get<ProjectTransitionReadinessResponse>(
    `/projects/${projectId}/start/check`
  )
  return data
}

export const startProjectTransition = async (
  projectId: number
): Promise<ProjectStartTransitionResponse> => {
  const { data } = await api.put<ProjectStartTransitionResponse>(
    `/projects/${projectId}/start`
  )
  return data
}

export const logout = (): void => {
  localStorage.removeItem('projectplanning_token')
  localStorage.removeItem('projectplanning_user_role')
}
