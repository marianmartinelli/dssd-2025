import {
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Button,
    List,
    Paper,
    Typography,
    Box,
    Chip,
    Stack,
    Divider,
} from '@mui/material'
import { format } from 'date-fns'
import type { ObservationResponse } from '../types/project'

interface ObservationsListModalProps {
    open: boolean
    observations: ObservationResponse[]
    onClose: () => void
    onResolve?: (observationId: number) => void
    isResolving?: number | null
}

export const ObservationsListModal = ({
    open,
    observations,
    onClose,
    onResolve,
    isResolving,
}: ObservationsListModalProps) => {
    // Ordenar observaciones por ID para mantener orden consistente
    const sortedObservations = [...observations].sort((a, b) => a.id - b.id)

    return (
        <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
            <DialogTitle>Observaciones del Proyecto</DialogTitle>
            <DialogContent>
                {sortedObservations.length === 0 ? (
                    <Box py={3} textAlign="center">
                        <Typography variant="body1" color="text.secondary">
                            No hay observaciones registradas para este proyecto.
                        </Typography>
                    </Box>
                ) : (
                    <List sx={{ pt: 0 }}>
                        {sortedObservations.map((observation, index) => (
                            <Box key={observation.id}>
                                {index > 0 && <Divider sx={{ my: 2 }} />}
                                <Paper variant="outlined" sx={{ p: 2 }}>
                                    <Stack spacing={2}>
                                        <Box display="flex" justifyContent="space-between" alignItems="flex-start">
                                            <Typography variant="h6" component="h3">
                                                {observation.title}
                                            </Typography>
                                            <Chip
                                                label={observation.isResolved ? 'Resuelta' : 'Pendiente'}
                                                color={observation.isResolved ? 'success' : 'warning'}
                                                size="small"
                                            />
                                        </Box>

                                        {observation.description && (
                                            <Typography variant="body2" color="text.secondary">
                                                {observation.description}
                                            </Typography>
                                        )}

                                        <Stack direction="row" spacing={3} flexWrap="wrap" alignItems="center">
                                            <Box>
                                                <Typography variant="caption" color="text.secondary">
                                                    Creado por:
                                                </Typography>
                                                <Typography variant="body2">
                                                    {observation.createdBy}
                                                </Typography>
                                            </Box>

                                            {observation.createdDate && (
                                                <Box>
                                                    <Typography variant="caption" color="text.secondary">
                                                        Fecha:
                                                    </Typography>
                                                    <Typography variant="body2">
                                                        {format(new Date(observation.createdDate), 'dd/MM/yyyy HH:mm')}
                                                    </Typography>
                                                </Box>
                                            )}
                                        </Stack>

                                        {!observation.isResolved && onResolve && (
                                            <Box display="flex" justifyContent="flex-end">
                                                <Button
                                                    variant="contained"
                                                    color="success"
                                                    size="small"
                                                    onClick={() => onResolve(observation.id)}
                                                    disabled={isResolving === observation.id}
                                                >
                                                    {isResolving === observation.id ? 'Marcando...' : 'Marcar como Resuelta'}
                                                </Button>
                                            </Box>
                                        )}
                                    </Stack>
                                </Paper>
                            </Box>
                        ))}
                    </List>
                )}
            </DialogContent>
            <DialogActions>
                <Button onClick={onClose}>Cerrar</Button>
            </DialogActions>
        </Dialog>
    )
}
