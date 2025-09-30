import axios from 'axios'
import type { ProjectFormValues, ProjectCreationResponse } from '../types/project'

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

export const login = async (username: string, password: string): Promise<void> => {
  const { data } = await api.post<{ access_token: string }>('/auth/login', { username, password })
  localStorage.setItem('projectplanning_token', data.access_token)
}

export const createProject = async (payload: ProjectFormValues): Promise<ProjectCreationResponse> => {
  const { data } = await api.post<ProjectCreationResponse>('/projects', payload)
  return data
}

export const logout = (): void => {
  localStorage.removeItem('projectplanning_token')
}
