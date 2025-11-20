import {
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Stack,
} from '@mui/material'
import type { SelectChangeEvent } from '@mui/material'
import type { ProjectStatus } from '../types/project'

interface ProjectFiltersProps {
  statusFilter?: ProjectStatus
  onStatusChange: (status?: ProjectStatus) => void
}

export const ProjectFilters = ({ statusFilter, onStatusChange }: ProjectFiltersProps) => {
  const handleStatusChange = (event: SelectChangeEvent<string>) => {
    const value = event.target.value
    onStatusChange(value === 'all' ? undefined : (value as ProjectStatus))
  }

  const clearFilters = () => {
    onStatusChange(undefined)
  }

  const hasActiveFilters = statusFilter !== undefined

  return (
    <Stack direction="row" spacing={2} alignItems="center">
      <FormControl size="small" sx={{ minWidth: 200 }}>
        <InputLabel id="status-filter-label">Estado</InputLabel>
        <Select
          labelId="status-filter-label"
          id="status-filter"
          value={statusFilter || 'all'}
          label="Estado"
          onChange={handleStatusChange}
        >
          <MenuItem value="all">Todos los estados</MenuItem>
          <MenuItem value="in_progress">En Progreso</MenuItem>
          <MenuItem value="completed">Completado</MenuItem>
          <MenuItem value="requesting_support">Solicitando Apoyo</MenuItem>
        </Select>
      </FormControl>

      {hasActiveFilters && (
        <Chip
          label="Limpiar filtros"
          onDelete={clearFilters}
          size="small"
          variant="outlined"
        />
      )}
    </Stack>
  )
}
