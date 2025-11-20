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

export const ProjectListPage = () => {
  const navigate = useNavigate()
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
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Stack spacing={3}>
        {/* Header */}
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="h4" component="h1">
            Proyectos
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleCreateProject}
          >
            Nuevo Proyecto
          </Button>
        </Box>

        {/* Tabs */}
        <Paper>
          <Tabs
            value={currentTab}
            onChange={handleTabChange}
            aria-label="project tabs"
          >
            <Tab label="Todos los Proyectos" value={0} />
            <Tab label="Mis Proyectos" value={1} />
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
          <Grid container spacing={3}>
            {projects?.map((project) => (
              <Grid item xs={12} sm={6} md={4} key={project.id}>
                <ProjectCard project={project} />
              </Grid>
            ))}
          </Grid>
        )}
      </Stack>
    </Container>
  )
}
