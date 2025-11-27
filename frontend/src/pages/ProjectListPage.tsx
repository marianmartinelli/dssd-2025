import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Container,
  Typography,
  Button,
  CircularProgress,
  Alert,
  Grid,
  Tabs,
  Tab,
  Stack,
  Paper,
} from '@mui/material'
import { Add as AddIcon } from '@mui/icons-material'
import { useProjects } from '../hooks/useProjects'
import { ProjectCard } from '../components/ProjectCard'
import { ProjectFilters } from '../components/ProjectFilters'
import type { ProjectStatus } from '../types/project'
import { useRoleAccess } from '../hooks/useRoleAccess'

export const ProjectListPage = () => {
  const navigate = useNavigate()
  const { isONG } = useRoleAccess()
  const [currentTab, setCurrentTab] = useState<0 | 1>(0)
  const [statusFilter, setStatusFilter] = useState<ProjectStatus | undefined>()

  const ownerOnly = currentTab === 1

  const { data: projects, isLoading, error } = useProjects({ statusFilter, ownerOnly })

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue as 0 | 1)
  }

  const handleCreateProject = () => {
    navigate('/projects/create')
  }

  if (isLoading) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress />
        </Box>
      </Container>
    )
  }

  if (error) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Alert severity="error">
          Error al cargar proyectos: {error.message}
        </Alert>
      </Container>
    )
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4, minWidth: { sm: '600px', md: '900px', lg: '1200px' } }}>
      <Stack spacing={3}>
        {/* Header */}
        <Stack
          direction={{ xs: 'column', sm: 'row' }}
          justifyContent="space-between"
          alignItems={{ xs: 'stretch', sm: 'center' }}
          spacing={2}
        >
          <Typography variant="h4" component="h1">
            Proyectos
          </Typography>
          {isONG && (
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={handleCreateProject}
              sx={{ width: { xs: '100%', sm: 'auto' } }}
            >
              Nuevo Proyecto
            </Button>
          )}
        </Stack>

        {/* Tabs */}
        <Paper>
          <Tabs
            value={currentTab}
            onChange={handleTabChange}
            aria-label="project tabs"
          >
            <Tab label="Todos los Proyectos" value={0} />
            {isONG && <Tab label="Mis Proyectos" value={1} />}
          </Tabs>
        </Paper>

        {/* Filters */}
        <Box>
          <ProjectFilters
            statusFilter={statusFilter}
            onStatusChange={setStatusFilter}
          />
        </Box>

        {/* Projects Grid */}
        {projects && projects.length === 0 ? (
          <Alert severity="info">
            {currentTab === 1
              ? 'No tienes proyectos creados. Haz clic en "Nuevo Proyecto" para crear uno.'
              : 'No hay proyectos disponibles.'}
          </Alert>
        ) : (
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', lg: 'repeat(3, 1fr)' }, gap: 3 }}>
            {projects?.map((project) => (
              <ProjectCard key={project.id} project={project} />
            ))}
          </Box>
        )}
      </Stack>
    </Container>
  )
}
