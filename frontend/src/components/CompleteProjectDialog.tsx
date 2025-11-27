import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Alert,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
} from '@mui/material'
import { CheckCircle } from '@mui/icons-material'
import type { WorkPlanStageResponse } from '../types/project'

interface CompleteProjectDialogProps {
  open: boolean
  projectName: string
  stages: WorkPlanStageResponse[]
  onConfirm: () => void
  onCancel: () => void
}

export const CompleteProjectDialog = ({
  open,
  projectName,
  stages,
  onConfirm,
  onCancel,
}: CompleteProjectDialogProps) => {
  const allStagesCompleted = stages.every(s => s.isCompleted)
  const completedCount = stages.filter(s => s.isCompleted).length

  return (
    <Dialog open={open} onClose={onCancel} maxWidth="md" fullWidth>
      <DialogTitle>Completar Proyecto: {projectName}</DialogTitle>
      <DialogContent>
        <Box mb={2}>
          <Typography variant="body1" gutterBottom>
            Estás por marcar este proyecto como <strong>"Completado"</strong>.
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            Esta acción cambiará el estado del proyecto y ya no podrás realizar más modificaciones.
          </Typography>
        </Box>

        <Divider sx={{ my: 2 }} />

        <Box mb={2}>
          <Typography variant="h6" gutterBottom>
            Estado de las Etapas
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            {completedCount} de {stages.length} etapas completadas
          </Typography>

          {!allStagesCompleted && (
            <Alert severity="error" sx={{ mb: 2 }}>
              <Typography variant="body2" fontWeight="medium">
                ⚠️ No se puede completar: Hay etapas pendientes
              </Typography>
              <Typography variant="caption" display="block" mt={1}>
                Debes completar todas las etapas antes de poder completar el proyecto.
              </Typography>
            </Alert>
          )}

          {allStagesCompleted && (
            <Alert severity="success" sx={{ mb: 2 }}>
              <Typography variant="body2" fontWeight="medium">
                ✓ Todas las etapas están completadas
              </Typography>
            </Alert>
          )}
        </Box>

        {stages.length > 0 && (
          <List dense>
            {stages.map(stage => (
              <ListItem key={stage.id}>
                <ListItemIcon>
                  <CheckCircle color={stage.isCompleted ? 'success' : 'disabled'} />
                </ListItemIcon>
                <ListItemText
                  primary={stage.stageName}
                  secondary={stage.isCompleted ? 'Completada' : 'Pendiente'}
                />
              </ListItem>
            ))}
          </List>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={onCancel}>Cancelar</Button>
        <Button
          onClick={onConfirm}
          variant="contained"
          color="primary"
          disabled={!allStagesCompleted}
        >
          Completar Proyecto
        </Button>
      </DialogActions>
    </Dialog>
  )
}
