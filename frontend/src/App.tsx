import { useMemo, useState } from 'react'
import type { JSX } from 'react'
import {
  AppBar,
  Toolbar,
  Typography,
  Container,
  Box,
  Button,
  Snackbar,
  Alert,
} from '@mui/material'
import type { AlertColor } from '@mui/material'
import { Logout } from '@mui/icons-material'
import { queryClient } from './lib/queryClient'
import { logout } from './api/bonita'
import { LoginForm } from './components/LoginForm'
import { ProjectCreatePage } from './pages/ProjectCreatePage'

type SnackbarState = {
  open: boolean
  message: string
  severity: AlertColor
}

function App(): JSX.Element {
  const [isAuthenticated, setIsAuthenticated] = useState(() => !!localStorage.getItem('projectplanning_token'))
  const [snackbar, setSnackbar] = useState<SnackbarState>({
    open: false,
    message: '',
    severity: 'success',
  })

  const handleLoginSuccess = () => {
    setIsAuthenticated(true)
    setSnackbar({
      open: true,
      message: 'Inicio de sesión exitoso',
      severity: 'success',
    })
  }

  const handleLogout = () => {
    logout()
    queryClient.clear()
    setIsAuthenticated(false)
    setSnackbar({
      open: true,
      message: 'Sesión finalizada',
      severity: 'info',
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

  const content = useMemo(() => {
    if (!isAuthenticated) {
      return (
        <Box display="flex" minHeight="80vh" justifyContent="center" alignItems="center">
          <LoginForm onSuccess={handleLoginSuccess} onError={handleShowMessage} />
        </Box>
      )
    }

    return <ProjectCreatePage onShowMessage={handleShowMessage} />
  }, [isAuthenticated])

  return (
    <Box minHeight="100vh" display="flex" flexDirection="column" bgcolor="background.default">
      <AppBar position="static" elevation={0} color="primary">
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            ProjectPlanning · Alta de Proyectos
          </Typography>
          {isAuthenticated && (
            <Button color="inherit" startIcon={<Logout />} onClick={handleLogout}>
              Cerrar sesión
            </Button>
          )}
        </Toolbar>
      </AppBar>

      <Box 
        sx={{ 
          display: 'flex', 
          justifyContent: 'center',
          width: '100%',
          flexGrow: 1
        }}
      >
        <Container 
          maxWidth="md" 
          sx={{ 
            py: { xs: 3, sm: 4, md: 6 }, 
            px: { xs: 2, sm: 3 },
            display: 'flex',
            flexDirection: 'column'
          }}
        >
          {content}
        </Container>
      </Box>

      <Box component="footer" py={3} textAlign="center" bgcolor="background.paper">
        <Typography variant="body2" color="text.secondary">
          Entrega 2 · Desarrollo de Software en Sistemas Distribuidos · 2025
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
  )
}

export default App
