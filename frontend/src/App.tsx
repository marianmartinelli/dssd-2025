import { useState } from 'react'
import type { JSX } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import {
  AppBar,
  Toolbar,
  Typography,
  Container,
  Box,
  Button,
  Snackbar,
  Alert,
  Chip,
} from '@mui/material'
import type { AlertColor } from '@mui/material'
import { Logout } from '@mui/icons-material'
import { queryClient } from './lib/queryClient'
import { logout as apiLogout } from './api/bonita'
import { LoginForm } from './components/LoginForm'
import { ProjectCreatePage } from './pages/ProjectCreatePage'
import { ProjectListPage } from './pages/ProjectListPage'
import { ProjectDetailPage } from './pages/ProjectDetailPage'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import MetricsDashboard from './pages/MetricsDashboard'
import { useRoleAccess } from './hooks/useRoleAccess'


type SnackbarState = {
  open: boolean
  message: string
  severity: AlertColor
}

const AppBarWithRole = () => {
  const { isAuthenticated, userRole, username, logout } = useAuth()

  const handleLogout = () => {
    apiLogout()
    logout()
    queryClient.clear()
  }

  return (
    <AppBar position="static" elevation={0} color="primary">
      <Toolbar>
        <Typography variant="h6" sx={{ flexGrow: 1 }}>
          ProjectPlanning
        </Typography>
        {isAuthenticated && userRole && (
          <Chip
            label={userRole}
            color="secondary"
            size="small"
            sx={{ mr: 2, fontWeight: 'bold' }}
          />
        )}
        {isAuthenticated && username && (
          <Typography variant="body2" sx={{ mr: 2, opacity: 0.9 }}>
            {username}
          </Typography>
        )}
        {isAuthenticated && (
          <Button color="inherit" startIcon={<Logout />} onClick={handleLogout}>
            Cerrar sesión
          </Button>
        )}
      </Toolbar>
    </AppBar>
  )
}

function AppContent(): JSX.Element {
  const { isAuthenticated } = useAuth()
  const [snackbar, setSnackbar] = useState<SnackbarState>({
    open: false,
    message: '',
    severity: 'success',
  })

  const handleLoginSuccess = () => {
    setSnackbar({
      open: true,
      message: 'Inicio de sesión exitoso',
      severity: 'success',
    })
  }

  const handleShowMessage = (message: string, severity: AlertColor = 'success') => {
    setSnackbar({
      open: true,
      message,
      severity,
    })
  }

  const handleCloseSnackbar = () => {
    setSnackbar((prev) => ({ ...prev, open: false }))
  }

  const ProtectedRoute = ({ children }: { children: JSX.Element }) => {
    if (!isAuthenticated) {
      return <Navigate to="/login" replace />
    }
    return children
  }

  const LoginRoute = () => {
    
    if (isAuthenticated) {
      const { hasRole } = useRoleAccess()
      if (hasRole('Gerente')) {
        return <Navigate to="/metrics" replace />
      }
      return <Navigate to="/projects" replace />
    }
    return (
      <Box display="flex" minHeight="80vh" justifyContent="center" alignItems="center">
        <LoginForm onSuccess={handleLoginSuccess} onError={handleShowMessage} />
      </Box>
    )
  }

  return (
    <BrowserRouter>
      <Box minHeight="100vh" display="flex" flexDirection="column" bgcolor="background.default">
        <AppBarWithRole />

        <Box
          sx={{
            display: 'flex',
            justifyContent: 'center',
            width: '100%',
            flexGrow: 1
          }}
        >
          <Routes>
            <Route path="/login" element={<LoginRoute />} />
            <Route
              path="/projects"
              element={
                <ProtectedRoute>
                  <ProjectListPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/projects/create"
              element={
                <ProtectedRoute>
                  <Container
                    maxWidth="md"
                    sx={{
                      py: { xs: 3, sm: 4, md: 6 },
                      px: { xs: 2, sm: 3 },
                      display: 'flex',
                      flexDirection: 'column'
                    }}
                  >
                    <ProjectCreatePage onShowMessage={handleShowMessage} />
                  </Container>
                </ProtectedRoute>
              }
            />
            <Route
              path="/projects/:projectId"
              element={
                <ProtectedRoute>
                  <ProjectDetailPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/metrics"
              element={
                <ProtectedRoute>
                  <MetricsDashboard />
                </ProtectedRoute>
              }
            />
            <Route path="/" element={<Navigate to={isAuthenticated ? "/projects" : "/login"} replace />} />
          </Routes>
        </Box>

        <Box component="footer" py={3} textAlign="center" bgcolor="background.paper">
          <Typography variant="body2" color="text.secondary">
            Desarrollo de Software en Sistemas Distribuidos · 2025
          </Typography>
        </Box>

        <Snackbar
          open={snackbar.open}
          autoHideDuration={4000}
          onClose={handleCloseSnackbar}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        >
          <Alert onClose={handleCloseSnackbar} severity={snackbar.severity} variant="filled" sx={{ width: '100%' }}>
            {snackbar.message}
          </Alert>
        </Snackbar>
      </Box>
    </BrowserRouter>
  )
}

function App(): JSX.Element {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  )
}

export default App
