import {
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Button,
    Box,
    Typography,
    Paper,
    Chip,
    Grid,
    Stack,
    Divider,
} from '@mui/material'
import { format } from 'date-fns'
import type { CollaborationRequestResponse } from '../types/project'

interface CollaborationRequestsListModalProps {
    open: boolean
    stageName: string
    collaborationRequests: CollaborationRequestResponse[]
    onClose: () => void
    onApprove: (collaborationId: number) => void
    onComplete: (collaborationId: number) => void
    isApproving: number | null
    isCompleting: number | null
}

export const CollaborationRequestsListModal = ({
    open,
    stageName,
    collaborationRequests,
    onClose,
    onApprove,
    onComplete,
    isApproving,
    isCompleting,
}: CollaborationRequestsListModalProps) => {
    return (
        <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
            <DialogTitle>
                Compromisos de Colaboración - Etapa: {stageName}
            </DialogTitle>
            <DialogContent>
                {collaborationRequests.length === 0 ? (
                    <Box py={3} textAlign="center">
                        <Typography color="text.secondary">
                            No hay compromisos de colaboración para esta etapa
                        </Typography>
                    </Box>
                ) : (
                    <Stack spacing={2} mt={1}>
                        {collaborationRequests.map((request) => (
                            <Paper key={request.id} variant="outlined" sx={{ p: 2 }}>
                                <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
                                    <Typography variant="h6" component="h3">
                                        {request.title}
                                    </Typography>
                                    <Stack direction="row" spacing={1}>
                                        {request.isCompleted && (
                                            <Chip label="Completado" color="success" size="small" />
                                        )}
                                        {request.isApproved && !request.isCompleted && (
                                            <Chip label="Aprobado" color="info" size="small" />
                                        )}
                                        {!request.isApproved && !request.isCompleted && (
                                            <Chip label="Pendiente" color="warning" size="small" />
                                        )}
                                    </Stack>
                                </Box>

                                {request.description && (
                                    <>
                                        <Typography variant="body2" color="text.secondary" paragraph>
                                            {request.description}
                                        </Typography>
                                        <Divider sx={{ my: 1.5 }} />
                                    </>
                                )}

                                <Grid container spacing={2}>
                                    {request.requestedAmount !== undefined && request.requestedAmount !== null && (
                                        <Grid item xs={12} sm={6}>
                                            <Typography variant="caption" color="text.secondary" display="block">
                                                Monto solicitado
                                            </Typography>
                                            <Typography variant="body2" fontWeight="medium">
                                                {request.amountCurrency} {request.requestedAmount.toLocaleString()}
                                            </Typography>
                                        </Grid>
                                    )}

                                    <Grid item xs={12} sm={6}>
                                        <Typography variant="caption" color="text.secondary" display="block">
                                            Solicitado por
                                        </Typography>
                                        <Typography variant="body2" fontWeight="medium">
                                            {request.committedBy}
                                        </Typography>
                                    </Grid>

                                    {request.requestedDate && (
                                        <Grid item xs={12} sm={6}>
                                            <Typography variant="caption" color="text.secondary" display="block">
                                                Fecha de solicitud
                                            </Typography>
                                            <Typography variant="body2">
                                                {format(new Date(request.requestedDate), 'dd/MM/yyyy HH:mm')}
                                            </Typography>
                                        </Grid>
                                    )}
                                </Grid>

                                {/* Botones de acción */}
                                <Box mt={2} display="flex" gap={1} justifyContent="flex-end">
                                    {!request.isApproved && (
                                        <Button
                                            variant="contained"
                                            color="primary"
                                            size="small"
                                            onClick={() => onApprove(request.id)}
                                            disabled={isApproving === request.id}
                                        >
                                            {isApproving === request.id ? 'Aprobando...' : 'Aprobar'}
                                        </Button>
                                    )}
                                    {request.isApproved && !request.isCompleted && (
                                        <Button
                                            variant="contained"
                                            color="success"
                                            size="small"
                                            onClick={() => onComplete(request.id)}
                                            disabled={isCompleting === request.id}
                                        >
                                            {isCompleting === request.id ? 'Completando...' : 'Completar'}
                                        </Button>
                                    )}
                                </Box>
                            </Paper>
                        ))}
                    </Stack>
                )}
            </DialogContent>
            <DialogActions>
                <Button onClick={onClose}>Cerrar</Button>
            </DialogActions>
        </Dialog>
    )
}
