import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
    Container,
    Paper,
    Typography,
    Box,
    Chip,
    Stack,
    Grid,
    Divider,
    Button,
    CircularProgress,
    Alert,
    Tooltip,
} from '@mui/material'
import { ArrowBack } from '@mui/icons-material'
import { format } from 'date-fns'
import { fetchProjectById, resolveObservation, fetchCollaborationRequests, approveCollaboration, completeCollaboration, completeStage, completeProject, fetchCurrentUser, startProjectTransition, checkProjectTransitionReadiness } from '../api/bonita'
import { ObservationModal } from '../components/ObservationModal'
import { ObservationsListModal } from '../components/ObservationsListModal'
import { CollaborationRequestsListModal } from '../components/CollaborationRequestsListModal'
import { CreateCollaborationModal } from '../components/CreateCollaborationModal'
import { StartProjectDialog } from '../components/StartProjectDialog'
import { CompleteProjectDialog } from '../components/CompleteProjectDialog'
import type { ProjectStatus, CollaborationRequestResponse, WorkPlanStageResponse, ProjectStartTransitionResponse, ProjectTransitionReadinessResponse } from '../types/project'

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

export const ProjectDetailPage = () => {
    const { projectId } = useParams<{ projectId: string }>()
    const navigate = useNavigate()
    const queryClient = useQueryClient()
    const [observationModalOpen, setObservationModalOpen] = useState(false)
    const [observationsListModalOpen, setObservationsListModalOpen] = useState(false)
    const [collaborationsModalOpen, setCollaborationsModalOpen] = useState(false)
    const [selectedStageId, setSelectedStageId] = useState<number | null>(null)
    const [selectedStageName, setSelectedStageName] = useState<string>('')
    const [snackbar, setSnackbar] = useState<{ message: string; severity: 'success' | 'error' } | null>(null)
    const [createCollabModalOpen, setCreateCollabModalOpen] = useState(false)
    const [createCollabStageId, setCreateCollabStageId] = useState<number | null>(null)
    const [createCollabStageName, setCreateCollabStageName] = useState<string>('')
    const [startProjectDialogOpen, setStartProjectDialogOpen] = useState(false)
    const [transitionInfo, setTransitionInfo] = useState<ProjectTransitionReadinessResponse | null>(null)
    const [completeProjectDialogOpen, setCompleteProjectDialogOpen] = useState(false)

    const { data: project, isLoading, error } = useQuery({
        queryKey: ['project', projectId],
        queryFn: () => fetchProjectById(Number(projectId)),
        enabled: !!projectId,
    })

    const { data: collaborationRequests = [] } = useQuery({
        queryKey: ['collaborations', projectId, selectedStageId],
        queryFn: () => fetchCollaborationRequests(Number(projectId)),
        enabled: !!projectId && collaborationsModalOpen,
    })

    const { data: currentUser } = useQuery({
        queryKey: ['currentUser'],
        queryFn: fetchCurrentUser,
        staleTime: 5 * 60 * 1000,
    })

    const resolveMutation = useMutation({
        mutationFn: resolveObservation,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['project', projectId] })
            setSnackbar({ message: 'Observación marcada como resuelta', severity: 'success' })
        },
        onError: () => {
            setSnackbar({ message: 'Error al marcar la observación como resuelta', severity: 'error' })
        },
    })

    const approveMutation = useMutation({
        mutationFn: approveCollaboration,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['collaborations', projectId, selectedStageId] })
            setSnackbar({ message: 'Pedido de colaboración aprobado', severity: 'success' })
        },
        onError: () => {
            setSnackbar({ message: 'Error al aprobar el pedido de colaboración', severity: 'error' })
        },
    })

    const completeMutation = useMutation({
        mutationFn: completeCollaboration,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['collaborations', projectId, selectedStageId] })
            setSnackbar({ message: 'Pedido de colaboración completado', severity: 'success' })
        },
        onError: () => {
            setSnackbar({ message: 'Error al completar el pedido de colaboración', severity: 'error' })
        },
    })

    const startProjectMutation = useMutation({
        mutationFn: startProjectTransition,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['project', projectId] })
            queryClient.invalidateQueries({ queryKey: ['projects'] })
            setStartProjectDialogOpen(false)
            setTransitionInfo(null)
            setSnackbar({
                message: 'Proyecto iniciado exitosamente. Ya no se pueden crear nuevas colaboraciones.',
                severity: 'success'
            })
        },
        onError: (error: any) => {
            const message = error.response?.data?.detail || 'Error al iniciar el proyecto'
            setSnackbar({ message, severity: 'error' })
            setStartProjectDialogOpen(false)
            setTransitionInfo(null)
        },
    })

    const completeStageMutation = useMutation({
        mutationFn: completeStage,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['project', projectId] })
            queryClient.invalidateQueries({ queryKey: ['projects'] })
            queryClient.invalidateQueries({ queryKey: ['collaborations', projectId, selectedStageId] })
            setSnackbar({ message: 'Etapa completada exitosamente', severity: 'success' })
        },
        onError: (error: any) => {
            const message = error.response?.data?.detail || 'Error al completar la etapa'
            setSnackbar({ message, severity: 'error' })
        },
    })

    const completeProjectMutation = useMutation({
        mutationFn: completeProject,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['project', projectId] })
            queryClient.invalidateQueries({ queryKey: ['projects'] })
            setCompleteProjectDialogOpen(false)
            setSnackbar({
                message: '¡Proyecto completado exitosamente! Felicitaciones.',
                severity: 'success'
            })
        },
        onError: (error: any) => {
            const message = error.response?.data?.detail || 'Error al completar el proyecto'
            setSnackbar({ message, severity: 'error' })
        },
    })

    const handleResolveObservation = (observationId: number) => {
        resolveMutation.mutate(observationId)
    }

    const handleApproveCollaboration = (collaborationId: number) => {
        approveMutation.mutate(collaborationId)
    }

    const handleCompleteCollaboration = (collaborationId: number) => {
        completeMutation.mutate(collaborationId)
    }

    const handleOpenCollaborationsModal = (stageId: number, stageName: string) => {
        setSelectedStageId(stageId)
        setSelectedStageName(stageName)
        // Invalidar la query para forzar un fetch fresco
        queryClient.invalidateQueries({ queryKey: ['collaborations', projectId, stageId] })
        setCollaborationsModalOpen(true)
    }

    const handleCloseCollaborationsModal = () => {
        setCollaborationsModalOpen(false)
        setSelectedStageId(null)
        setSelectedStageName('')
    }

    const handleOpenCreateCollabModal = (stageId: number, stageName: string) => {
        setCreateCollabStageId(stageId)
        setCreateCollabStageName(stageName)
        setCreateCollabModalOpen(true)
    }

    const handleCloseCreateCollabModal = () => {
        setCreateCollabModalOpen(false)
        setCreateCollabStageId(null)
        setCreateCollabStageName('')
    }

    const handleOpenStartProjectDialog = async () => {
        try {
            const info = await checkProjectTransitionReadiness(Number(projectId))
            setTransitionInfo(info)
            setStartProjectDialogOpen(true)
        } catch (error: any) {
            const message = error.response?.data?.detail || 'Error al verificar el estado del proyecto'
            setSnackbar({ message, severity: 'error' })
        }
    }

    const handleConfirmStartProject = () => {
        if (projectId) {
            startProjectMutation.mutate(Number(projectId))
        }
    }

    const handleCancelStartProject = () => {
        setStartProjectDialogOpen(false)
        setTransitionInfo(null)
    }

    const handleCompleteStage = (stageId: number) => {
        completeStageMutation.mutate(stageId)
    }

    const handleOpenCompleteProjectDialog = () => {
        setCompleteProjectDialogOpen(true)
    }

    const handleCloseCompleteProjectDialog = () => {
        setCompleteProjectDialogOpen(false)
    }

    const handleConfirmCompleteProject = () => {
        if (projectId) {
            completeProjectMutation.mutate(Number(projectId))
        }
    }

    const isOwner = currentUser?.username === project?.initiatorUserId

    // Filtrar Compromisos de Colaboración por la etapa seleccionada
    const filteredCollaborations = collaborationRequests.filter(
        (req: CollaborationRequestResponse) => {
            return req.work_plan_stage_id === selectedStageId
        }
    )

    if (isLoading) {
        return (
            <Container maxWidth="lg" sx={{ py: 4 }}>
                <Box display="flex" justifyContent="center" alignItems="center" minHeight="50vh">
                    <CircularProgress />
                </Box>
            </Container>
        )
    }

    if (error || !project) {
        return (
            <Container maxWidth="lg" sx={{ py: 4 }}>
                <Alert severity="error">
                    Error al cargar el proyecto. Por favor, intente nuevamente.
                </Alert>
                <Box mt={2}>
                    <Button startIcon={<ArrowBack />} onClick={() => navigate('/projects')}>
                        Volver a proyectos
                    </Button>
                </Box>
            </Container>
        )
    }

    return (
        <Container maxWidth="lg" sx={{ py: 4 }}>
            <Box mb={3}>
                <Button startIcon={<ArrowBack />} onClick={() => navigate('/projects')}>
                    Volver a proyectos
                </Button>
            </Box>

            <Paper sx={{ p: 3 }}>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2} flexWrap="wrap" gap={2}>
                    <Typography variant="h4" component="h1">
                        {project.projectName}
                    </Typography>
                    <Box display="flex" alignItems="center" gap={2}>
                        <Chip
                            label={getStatusLabel(project.status)}
                            color={getStatusColor(project.status)}
                            size="medium"
                        />
                        {isOwner && project.status === 'requesting_support' && (
                            <Button
                                variant="contained"
                                color="success"
                                onClick={handleOpenStartProjectDialog}
                            >
                                Iniciar Proyecto
                            </Button>
                        )}
                        {isOwner && project.status === 'in_progress' && (
                            <Button
                                variant="contained"
                                color="primary"
                                onClick={handleOpenCompleteProjectDialog}
                                disabled={completeProjectMutation.isPending}
                            >
                                {completeProjectMutation.isPending ? 'Completando...' : 'Completar Proyecto'}
                            </Button>
                        )}
                    </Box>
                </Box>

                <Box display="flex" justifyContent="center" gap={2} mb={3}>
                    <Button
                        variant="contained"
                        color="primary"
                        onClick={() => setObservationModalOpen(true)}
                    >
                        Registrar Observación
                    </Button>
                    <Button
                        variant="outlined"
                        color="primary"
                        onClick={() => setObservationsListModalOpen(true)}
                    >
                        Ver Observaciones {project.observations?.length ? `(${project.observations.length})` : ''}
                    </Button>
                </Box>

                <Divider sx={{ mb: 3 }} />

                <Grid container spacing={3}>
                    <Grid item xs={12}>
                        <Typography variant="h6" gutterBottom>
                            Descripción
                        </Typography>
                        <Typography variant="body1" color="text.secondary" paragraph>
                            {project.projectDescription || 'Sin descripción'}
                        </Typography>
                    </Grid>

                    <Grid item xs={12} md={6}>
                        <Typography variant="subtitle2" color="text.secondary">
                            Categoría
                        </Typography>
                        <Typography variant="body1">
                            {project.projectCategory || '-'}
                        </Typography>
                    </Grid>

                    <Grid item xs={12} md={6}>
                        <Typography variant="subtitle2" color="text.secondary">
                            Organización solicitante
                        </Typography>
                        <Typography variant="body1">
                            {project.requestingOrganization || '-'}
                        </Typography>
                    </Grid>

                    <Grid item xs={12} md={6}>
                        <Typography variant="subtitle2" color="text.secondary">
                            Email de contacto
                        </Typography>
                        <Typography variant="body1">
                            {project.contactEmail || '-'}
                        </Typography>
                    </Grid>

                    <Grid item xs={12} md={6}>
                        <Typography variant="subtitle2" color="text.secondary">
                            Teléfono de contacto
                        </Typography>
                        <Typography variant="body1">
                            {project.contactPhone || '-'}
                        </Typography>
                    </Grid>

                    <Grid item xs={12} md={6}>
                        <Typography variant="subtitle2" color="text.secondary">
                            Presupuesto estimado
                        </Typography>
                        <Typography variant="body1">
                            {project.estimatedBudget !== undefined
                                ? `${project.currency} ${project.estimatedBudget.toLocaleString()}`
                                : '-'}
                        </Typography>
                    </Grid>

                    <Grid item xs={12} md={6}>
                        <Typography variant="subtitle2" color="text.secondary">
                            Nivel de prioridad
                        </Typography>
                        <Typography variant="body1">
                            {project.priorityLevel || '-'}
                        </Typography>
                    </Grid>

                    <Grid item xs={12} md={6}>
                        <Typography variant="subtitle2" color="text.secondary">
                            Fecha de inicio
                        </Typography>
                        <Typography variant="body1">
                            {project.startDate ? format(new Date(project.startDate), 'dd/MM/yyyy') : '-'}
                        </Typography>
                    </Grid>

                    <Grid item xs={12} md={6}>
                        <Typography variant="subtitle2" color="text.secondary">
                            Fecha de finalización
                        </Typography>
                        <Typography variant="body1">
                            {project.endDate ? format(new Date(project.endDate), 'dd/MM/yyyy') : '-'}
                        </Typography>
                    </Grid>

                    {project.supportingDocsUrl && (
                        <Grid item xs={12}>
                            <Typography variant="subtitle2" color="text.secondary">
                                Documentos de apoyo
                            </Typography>
                            <Typography variant="body1">
                                <a href={project.supportingDocsUrl} target="_blank" rel="noopener noreferrer">
                                    {project.supportingDocsUrl}
                                </a>
                            </Typography>
                        </Grid>
                    )}

                    {project.submissionTimestamp && (
                        <Grid item xs={12} md={6}>
                            <Typography variant="subtitle2" color="text.secondary">
                                Fecha de presentación
                            </Typography>
                            <Typography variant="body1">
                                {format(new Date(project.submissionTimestamp), 'dd/MM/yyyy HH:mm')}
                            </Typography>
                        </Grid>
                    )}

                    {project.initiatorUserId && (
                        <Grid item xs={12} md={6}>
                            <Typography variant="subtitle2" color="text.secondary">
                                Usuario iniciador
                            </Typography>
                            <Typography variant="body1">
                                {project.initiatorUserId}
                            </Typography>
                        </Grid>
                    )}

                    {project.caseId !== undefined && (
                        <Grid item xs={12} md={6}>
                            <Typography variant="subtitle2" color="text.secondary">
                                ID de caso (Bonita)
                            </Typography>
                            <Typography variant="body1">
                                {project.caseId}
                            </Typography>
                        </Grid>
                    )}
                </Grid>

                {project.workPlanStages.length > 0 && (
                    <>
                        <Divider sx={{ my: 4 }} />
                        <Typography variant="h6" gutterBottom>
                            Plan de trabajo ({project.workPlanStages.length} etapa{project.workPlanStages.length !== 1 ? 's' : ''})
                        </Typography>
                        <Stack spacing={2} mt={2}>
                            {project.workPlanStages.map((stage: WorkPlanStageResponse) => (
                                <Paper key={stage.id} variant="outlined" sx={{ p: 2 }}>
                                    <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                                        <Typography variant="subtitle1" fontWeight="medium">
                                            {stage.stageName}
                                        </Typography>
                                        <Box display="flex" alignItems="center" gap={1}>
                                            {stage.isCompleted ? (
                                                <Chip label="Completada" color="success" size="small" />
                                            ) : (
                                                isOwner && project.status === 'in_progress' && (
                                                    <Button
                                                        variant="outlined"
                                                        color="success"
                                                        size="small"
                                                        onClick={() => handleCompleteStage(stage.id)}
                                                        disabled={completeStageMutation.isPending && completeStageMutation.variables === stage.id}
                                                    >
                                                        {completeStageMutation.isPending && completeStageMutation.variables === stage.id
                                                            ? 'Completando...'
                                                            : 'Completar Etapa'}
                                                    </Button>
                                                )
                                            )}
                                        </Box>
                                    </Box>
                                    {stage.description && (
                                        <Typography variant="body2" color="text.secondary" paragraph>
                                            {stage.description}
                                        </Typography>
                                    )}
                                    <Grid container spacing={2}>
                                        {stage.stageStart && stage.stageEnd && (
                                            <Grid item xs={12} sm={6}>
                                                <Typography variant="caption" color="text.secondary">
                                                    Periodo
                                                </Typography>
                                                <Typography variant="body2">
                                                    {format(new Date(stage.stageStart), 'dd/MM/yyyy')} -{' '}
                                                    {format(new Date(stage.stageEnd), 'dd/MM/yyyy')}
                                                </Typography>
                                            </Grid>
                                        )}
                                        {stage.supportType && (
                                            <Grid item xs={12} sm={6}>
                                                <Typography variant="caption" color="text.secondary">
                                                    Tipo de apoyo
                                                </Typography>
                                                <Typography variant="body2">
                                                    {stage.supportType}
                                                </Typography>
                                            </Grid>
                                        )}
                                        {stage.estimatedAmount != null && (
                                            <Grid item xs={12} sm={6}>
                                                <Typography variant="caption" color="text.secondary">
                                                    Monto estimado
                                                </Typography>
                                                <Typography variant="body2">
                                                    {stage.amountCurrency} {stage.estimatedAmount.toLocaleString()}
                                                </Typography>
                                            </Grid>
                                        )}
                                    </Grid>
                                    <Box mt={2} display="flex" justifyContent="flex-end" gap={1}>
                                        <Tooltip
                                            title={
                                                isOwner
                                                    ? "Los owners no pueden crear colaboraciones"
                                                    : project.status !== 'requesting_support'
                                                    ? "No se pueden crear colaboraciones en proyectos en progreso"
                                                    : ""
                                            }
                                            arrow
                                        >
                                            <span>
                                                <Button
                                                    variant="contained"
                                                    size="small"
                                                    disabled={isOwner || project.status !== 'requesting_support'}
                                                    onClick={() => handleOpenCreateCollabModal(stage.id, stage.stageName)}
                                                >
                                                    Crear Colaboración
                                                </Button>
                                            </span>
                                        </Tooltip>
                                        <Button
                                            variant="outlined"
                                            size="small"
                                            onClick={() => handleOpenCollaborationsModal(stage.id, stage.stageName)}
                                        >
                                            Ver Compromisos de Colaboración
                                        </Button>
                                    </Box>
                                </Paper>
                            ))}
                        </Stack>
                    </>
                )}
            </Paper>

            <ObservationModal
                open={observationModalOpen}
                projectId={Number(projectId)}
                onClose={() => setObservationModalOpen(false)}
                onSuccess={() => {
                    setSnackbar({ message: 'Observación registrada exitosamente', severity: 'success' })
                }}
                onError={(message) => {
                    setSnackbar({ message, severity: 'error' })
                }}
            />

            <ObservationsListModal
                open={observationsListModalOpen}
                observations={project.observations || []}
                onClose={() => setObservationsListModalOpen(false)}
                onResolve={handleResolveObservation}
                isResolving={resolveMutation.isPending ? resolveMutation.variables : null}
            />

            <CollaborationRequestsListModal
                open={collaborationsModalOpen}
                stageName={selectedStageName}
                collaborationRequests={filteredCollaborations}
                onClose={handleCloseCollaborationsModal}
                onApprove={handleApproveCollaboration}
                onComplete={handleCompleteCollaboration}
                isApproving={approveMutation.isPending ? approveMutation.variables : null}
                isCompleting={completeMutation.isPending ? completeMutation.variables : null}
                isOwner={isOwner}
                onCreateClick={() => handleOpenCreateCollabModal(selectedStageId!, selectedStageName)}
                currentUsername={currentUser?.username}
            />

            <CreateCollaborationModal
                open={createCollabModalOpen}
                projectId={Number(projectId)}
                stageId={createCollabStageId || 0}
                stageName={createCollabStageName}
                onClose={handleCloseCreateCollabModal}
                onSuccess={() => {
                    setSnackbar({
                        message: 'Compromiso de colaboración creado exitosamente',
                        severity: 'success'
                    })
                }}
                onError={(message) => {
                    setSnackbar({ message, severity: 'error' })
                }}
            />

            <StartProjectDialog
                open={startProjectDialogOpen}
                projectName={project.projectName}
                stagesCoverage={transitionInfo?.stagesCoverage || null}
                totalStages={transitionInfo?.totalStages || 0}
                coveredStages={transitionInfo?.coveredStages || 0}
                uncoveredStages={transitionInfo?.uncoveredStages || 0}
                isLoading={startProjectMutation.isPending}
                onConfirm={handleConfirmStartProject}
                onCancel={handleCancelStartProject}
            />

            <CompleteProjectDialog
                open={completeProjectDialogOpen}
                projectName={project.projectName}
                stages={project.workPlanStages}
                onConfirm={handleConfirmCompleteProject}
                onCancel={handleCloseCompleteProjectDialog}
            />

            {snackbar && (
                <Box
                    sx={{
                        position: 'fixed',
                        bottom: 16,
                        right: 16,
                        zIndex: 9999
                    }}
                >
                    <Alert
                        severity={snackbar.severity}
                        onClose={() => setSnackbar(null)}
                        sx={{ minWidth: 300 }}
                    >
                        {snackbar.message}
                    </Alert>
                </Box>
            )}
        </Container>
    )
}
