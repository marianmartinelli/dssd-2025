import {
  Card,
  CardContent,
  CardActionArea,
  Typography,
  Box,
  Chip,
  Stack,
} from '@mui/material'
import { format } from 'date-fns'
import { useNavigate } from 'react-router-dom'
import type { ProjectListItem, ProjectStatus } from '../types/project'

interface ProjectCardProps {
  project: ProjectListItem
}

const getStatusLabel = (status: ProjectStatus): string => {
  const labels: Record<ProjectStatus, string> = {
    in_progress: 'En Progreso',
    completed: 'Completado',
    requesting_support: 'Solicitando Apoyo',
  }
  return labels[status]
}

const getStatusColor = (status: ProjectStatus): 'info' | 'success' | 'warning' => {
  const colors: Record<ProjectStatus, 'info' | 'success' | 'warning'> = {
    in_progress: 'info',
    completed: 'success',
    requesting_support: 'warning',
  }
  return colors[status]
}

export const ProjectCard = ({ project }: ProjectCardProps) => {
  const navigate = useNavigate()

  const handleClick = () => {
    navigate(`/projects/${project.id}`)
  }

  return (
    <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <CardActionArea onClick={handleClick}>
        <CardContent>
        <Stack spacing={2}>
          <Box display="flex" justifyContent="space-between" alignItems="flex-start" gap={1}>
            <Typography
              variant="h6"
              component="h3"
              gutterBottom
              sx={{
                wordBreak: 'break-word',
                overflowWrap: 'break-word',
                hyphens: 'auto',
                flex: 1,
              }}
            >
              {project.projectName}
            </Typography>
            <Chip
              label={getStatusLabel(project.status)}
              color={getStatusColor(project.status)}
              size="small"
              sx={{ flexShrink: 0 }}
            />
          </Box>

          {project.projectDescription && (
            <Typography
              variant="body2"
              color="text.secondary"
              sx={{
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                display: '-webkit-box',
                WebkitLineClamp: 2,
                WebkitBoxOrient: 'vertical',
                wordBreak: 'break-word',
              }}
            >
              {project.projectDescription}
            </Typography>
          )}

          <Stack direction="row" spacing={2} flexWrap="wrap" sx={{ gap: 1 }}>
            {project.startDate && project.endDate && (
              <Box sx={{ minWidth: 0 }}>
                <Typography variant="caption" color="text.secondary" display="block">
                  Fechas:
                </Typography>
                <Typography variant="body2" sx={{ fontSize: { xs: '0.8rem', sm: '0.875rem' } }}>
                  {format(new Date(project.startDate), 'dd/MM/yyyy')} -{' '}
                  {format(new Date(project.endDate), 'dd/MM/yyyy')}
                </Typography>
              </Box>
            )}

            {project.estimatedBudget !== undefined && (
              <Box sx={{ minWidth: 0 }}>
                <Typography variant="caption" color="text.secondary" display="block">
                  Presupuesto:
                </Typography>
                <Typography variant="body2" sx={{ fontSize: { xs: '0.8rem', sm: '0.875rem' } }}>
                  {project.currency} {project.estimatedBudget.toLocaleString()}
                </Typography>
              </Box>
            )}
          </Stack>

          {project.workPlanStages.length > 0 && (
            <Typography variant="caption" color="text.secondary">
              {project.workPlanStages.length} etapa{project.workPlanStages.length !== 1 ? 's' : ''}
            </Typography>
          )}
        </Stack>
      </CardContent>
      </CardActionArea>
    </Card>
  )
}
