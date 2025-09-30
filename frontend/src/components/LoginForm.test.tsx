import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, cleanup } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ThemeProvider } from '@mui/material'
import { LoginForm } from './LoginForm'
import { theme } from '../theme'
import * as bonitaApi from '../api/bonita'

// Mock the API
vi.mock('../api/bonita', () => ({
  login: vi.fn(),
}))

const MockedLoginProvider = ({ children }: { children: React.ReactNode }) => (
  <ThemeProvider theme={theme}>{children}</ThemeProvider>
)

describe('LoginForm', () => {
  const mockOnSuccess = vi.fn()
  const mockOnError = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    cleanup()
  })

  it('renders login form with email and password fields', () => {
    const { container } = render(
      <MockedLoginProvider>
        <LoginForm onSuccess={mockOnSuccess} onError={mockOnError} />
      </MockedLoginProvider>
    )

    expect(container.querySelector('input[name="username"]')).toBeInTheDocument()
    expect(container.querySelector('input[name="password"]')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /ingresar/i })).toBeInTheDocument()
  })

  it('calls login API and onSuccess when valid credentials are submitted', async () => {
    const user = userEvent.setup()
    vi.mocked(bonitaApi.login).mockResolvedValue()

    const { container } = render(
      <MockedLoginProvider>
        <LoginForm onSuccess={mockOnSuccess} onError={mockOnError} />
      </MockedLoginProvider>
    )

    const emailField = container.querySelector('input[name="username"]') as HTMLInputElement
    const passwordField = container.querySelector('input[name="password"]') as HTMLInputElement
    
    await user.type(emailField, 'admin@example.org')
    await user.type(passwordField, 'admin123')
    await user.click(screen.getByRole('button', { name: /ingresar/i }))

    await waitFor(() => {
      expect(bonitaApi.login).toHaveBeenCalledWith('admin@example.org', 'admin123')
      expect(mockOnSuccess).toHaveBeenCalled()
    })
  })

  it('calls onError when login fails', async () => {
    const user = userEvent.setup()
    vi.mocked(bonitaApi.login).mockRejectedValue(new Error('Login failed'))

    const { container } = render(
      <MockedLoginProvider>
        <LoginForm onSuccess={mockOnSuccess} onError={mockOnError} />
      </MockedLoginProvider>
    )

    const emailField = container.querySelector('input[name="username"]') as HTMLInputElement
    const passwordField = container.querySelector('input[name="password"]') as HTMLInputElement
    
    await user.type(emailField, 'wrong@example.org')
    await user.type(passwordField, 'wrongpass')
    await user.click(screen.getByRole('button', { name: /ingresar/i }))

    await waitFor(() => {
      expect(mockOnError).toHaveBeenCalledWith('Credenciales inválidas o error de conexión.', 'error')
    })
  })
})
