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
  CircularProgress,
} from '@mui/material'
import { CheckCircle, Cancel } from '@mui/icons-material'
import type { StageCoverageInfo } from '../types/project'

interface StartProjectDialogProps {
  open: boolean
  projectName: string
  stagesCoverage: StageCoverageInfo[] | null
  totalStages: number
  coveredStages: number
  uncoveredStages: number
  isLoading: boolean
  onConfirm: () => void
  onCancel: () => void
}

export const StartProjectDialog = ({
  open,
  projectName,
  stagesCoverage,
  totalStages,
  coveredStages,
  uncoveredStages,
  isLoading,
  onConfirm,
  onCancel,
}: StartProjectDialogProps) => {
  const hasUncoveredStages = uncoveredStages > 0

  return (
    <Dialog open={open} onClose={onCancel} maxWidth="md" fullWidth>
      <DialogTitle>Iniciar Proyecto: {projectName}</DialogTitle>
      <DialogContent>
        <Box mb={2}>
          <Typography variant="body1" gutterBottom>
            Estás por cambiar el estado del proyecto de <strong>"Solicitando Apoyo"</strong> a{' '}
            <strong>"En Progreso"</strong>.
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            Una vez iniciado el proyecto, <strong>NO se podrán crear nuevas colaboraciones</strong>.
            Solo podrás trabajar con las colaboraciones ya aprobadas.
          </Typography>
        </Box>

        <Divider sx={{ my: 2 }} />

        <Box mb={2}>
          <Typography variant="h6" gutterBottom>
            Cobertura de Etapas
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            {coveredStages} de {totalStages} etapas tienen colaboraciones aprobadas
          </Typography>

          {hasUncoveredStages && (
            <Alert severity="warning" sx={{ mb: 2 }}>
              <Typography variant="body2" fontWeight="medium">
                ⚠️ Atención: {uncoveredStages} etapa{uncoveredStages !== 1 ? 's' : ''} sin
                colaboraciones aprobadas
              </Typography>
              <Typography variant="caption" display="block" mt={1}>
                Podrás continuar, pero estas etapas quedarán sin apoyo de colaboradores externos.
              </Typography>
            </Alert>
          )}

          {stagesCoverage && (
            <List dense>
              {stagesCoverage.map((stage) => (
                <ListItem key={stage.stageId}>
                  <ListItemIcon>
                    {stage.hasApprovedCollaboration ? (
                      <CheckCircle color="success" />
                    ) : (
                      <Cancel color="warning" />
                    )}
                  </ListItemIcon>
                  <ListItemText
                    primary={stage.stageName}
                    secondary={
                      stage.hasApprovedCollaboration
                        ? `${stage.approvedCount} colaboración${stage.approvedCount !== 1 ? 'es' : ''} aprobada${stage.approvedCount !== 1 ? 's' : ''}`
                        : 'Sin colaboraciones aprobadas'
                    }
                  />
                </ListItem>
              ))}
            </List>
          )}
        </Box>

        {hasUncoveredStages && (
          <Alert severity="info" sx={{ mt: 2 }}>
            <Typography variant="body2">
              💡 Sugerencia: Considera aprobar más colaboraciones antes de iniciar el proyecto para
              tener mejor cobertura en todas las etapas.
            </Typography>
          </Alert>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onCancel} disabled={isLoading}>
          Cancelar
        </Button>
        <Button
          onClick={onConfirm}
          variant="contained"
          color="primary"
          disabled={isLoading}
          startIcon={isLoading ? <CircularProgress size={20} /> : null}
        >
          {isLoading ? 'Iniciando...' : 'Confirmar e Iniciar Proyecto'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}
