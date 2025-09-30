import { useState } from 'react'
import type { AlertColor } from '@mui/material'
import {
  Box,
  Paper,
  Stack,
  Typography,
  TextField,
  MenuItem,
  Button,
  IconButton,
  Divider,
  Tooltip,
  Alert,
} from '@mui/material'
import { Add, DeleteOutline, Save } from '@mui/icons-material'
import { useForm, useFieldArray, type SubmitHandler } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import type { ProjectFormValues, ProjectCreationResponse, WorkPlanStageForm } from '../types/project'
import { projectSchema } from '../lib/validation'
import { useCreateProject } from '../hooks/useCreateProject'

const createDefaultStage = (): WorkPlanStageForm => ({
  stageName: '',
  stageStart: '',
  stageEnd: '',
  supportType: 'financial',
  description: '',
  estimatedAmount: undefined,
  amountCurrency: undefined,
})

const createDefaultValues = (): ProjectFormValues => ({
  projectName: '',
  projectDescription: '',
  projectCategory: '',
  requestingOrganization: '',
  contactEmail: '',
  contactPhone: '',
  estimatedBudget: 0,
  currency: 'USD',
  startDate: '',
  endDate: '',
  priorityLevel: 'medium',
  supportingDocsUrl: '',
  workPlanStages: [createDefaultStage()],
})

interface ProjectCreatePageProps {
  onShowMessage: (message: string, severity?: AlertColor) => void
}

export const ProjectCreatePage = ({ onShowMessage }: ProjectCreatePageProps) => {
  const [lastResult, setLastResult] = useState<ProjectCreationResponse | null>(null)

  const {
    control,
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(projectSchema),
    defaultValues: createDefaultValues(),
    mode: 'onBlur',
  })

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'workPlanStages',
  })

  const createProjectMutation = useCreateProject()

  const onSubmit: SubmitHandler<ProjectFormValues> = async (values) => {
    try {
      const response = await createProjectMutation.mutateAsync(values)
      setLastResult(response)
      onShowMessage(`Caso creado en Bonita · Case ID ${response.caseId}`, 'success')
      reset(createDefaultValues())
    } catch (error) {
      console.error(error)
      onShowMessage('No se pudo crear el proyecto. Reintente más tarde.', 'error')
    }
  }

  const handleAddStage = () => {
    append(createDefaultStage())
  }

  const handleRemoveStage = (index: number) => {
    if (fields.length === 1) {
      onShowMessage('Debe existir al menos una etapa en el plan de trabajo.', 'warning')
      return
    }
    remove(index)
  }

  const isLoading = isSubmitting || createProjectMutation.isPending

  return (
    <Box component="section">
      <Typography variant="h4" gutterBottom>
        Alta de proyecto
      </Typography>
      <Typography variant="body1" color="text.secondary" mb={4}>
        Complete la información del proyecto y las etapas del plan de trabajo. Al enviar, se iniciará la instancia del
        proceso en Bonita con el volumen de datos requerido.
      </Typography>

      <Box component="form" onSubmit={handleSubmit(onSubmit)} noValidate>
        <Stack spacing={4}>
          <Paper elevation={2} sx={{ p: { xs: 2, sm: 3 } }}>
            <Typography variant="h6" gutterBottom>
              Información general
            </Typography>
              <Stack spacing={2}>
                <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
                  <TextField
                    label="Nombre del proyecto"
                    placeholder="Mejora de infraestructura comunitaria"
                    fullWidth
                    {...register('projectName')}
                    error={!!errors.projectName}
                    helperText={errors.projectName?.message}
                  />
                  <TextField
                    label="Categoría"
                    placeholder="Infraestructura / Energía / Salud"
                    fullWidth
                    {...register('projectCategory')}
                    error={!!errors.projectCategory}
                    helperText={errors.projectCategory?.message}
                  />
                </Stack>
              <TextField
                label="Descripción"
                placeholder="Breve resumen del objetivo, alcance y resultados esperados..."
                fullWidth
                multiline
                minRows={4}
                {...register('projectDescription')}
                error={!!errors.projectDescription}
                helperText={errors.projectDescription?.message}
              />
              <Stack spacing={2}>
                <TextField
                  label="Organización solicitante"
                  placeholder="ONG Hope Builders"
                  fullWidth
                  {...register('requestingOrganization')}
                  error={!!errors.requestingOrganization}
                  helperText={errors.requestingOrganization?.message}
                />
                <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
                  <TextField
                    label="Email de contacto"
                    placeholder="contacto@ong.org"
                    fullWidth
                    {...register('contactEmail')}
                    error={!!errors.contactEmail}
                    helperText={errors.contactEmail?.message}
                  />
                  <TextField
                    label="Teléfono"
                    placeholder="+54 11 5555-5555"
                    fullWidth
                    {...register('contactPhone')}
                    error={!!errors.contactPhone}
                    helperText={errors.contactPhone?.message}
                  />
                </Stack>
              </Stack>
              <Stack spacing={2}>
                <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
                  <TextField
                    label="Presupuesto estimado"
                    type="number"
                    inputProps={{ min: 0, step: 1000 }}
                    fullWidth
                    {...register('estimatedBudget', { valueAsNumber: true })}
                    error={!!errors.estimatedBudget}
                    helperText={errors.estimatedBudget?.message}
                  />
                  <TextField
                    label="Moneda"
                    placeholder="USD"
                    inputProps={{ maxLength: 3 }}
                    fullWidth
                    {...register('currency')}
                    error={!!errors.currency}
                    helperText={errors.currency?.message}
                  />
                </Stack>
                <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
                  <TextField
                    label="Fecha de inicio"
                    type="date"
                    fullWidth
                    InputLabelProps={{ shrink: true }}
                    {...register('startDate')}
                    error={!!errors.startDate}
                    helperText={errors.startDate?.message}
                  />
                  <TextField
                    label="Fecha de fin"
                    type="date"
                    fullWidth
                    InputLabelProps={{ shrink: true }}
                    {...register('endDate')}
                    error={!!errors.endDate}
                    helperText={errors.endDate?.message}
                  />
                </Stack>
              </Stack>
              <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
                <TextField select label="Prioridad" fullWidth defaultValue="medium" {...register('priorityLevel')}>
                  <MenuItem value="low">Baja</MenuItem>
                  <MenuItem value="medium">Media</MenuItem>
                  <MenuItem value="high">Alta</MenuItem>
                  <MenuItem value="critical">Crítica</MenuItem>
                </TextField>
                <TextField
                  label="URL documentación de respaldo (opcional)"
                  placeholder="https://drive.google.com/..."
                  fullWidth
                  {...register('supportingDocsUrl')}
                  error={!!errors.supportingDocsUrl}
                  helperText={errors.supportingDocsUrl?.message}
                />
              </Stack>
            </Stack>
          </Paper>

          <Paper elevation={2} sx={{ p: { xs: 2, sm: 3 } }}>
            <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">Plan de trabajo</Typography>
              <Button variant="outlined" startIcon={<Add />} onClick={handleAddStage}>
                Agregar etapa
              </Button>
            </Stack>

            <Stack spacing={2}>
              {fields.map((field, index) => (
                <Paper key={field.id} variant="outlined" sx={{ p: 2 }}>
                  <Stack spacing={2}>
                    <Stack direction="row" justifyContent="space-between" alignItems="center">
                      <Typography variant="subtitle1">Etapa {index + 1}</Typography>
                      <Tooltip title="Eliminar etapa">
                        <span>
                          <IconButton
                            aria-label="Eliminar etapa"
                            onClick={() => handleRemoveStage(index)}
                            disabled={fields.length === 1}
                          >
                            <DeleteOutline />
                          </IconButton>
                        </span>
                      </Tooltip>
                    </Stack>
                    <Divider />
                    <Stack spacing={2}>
                      <Stack spacing={2}>
                        <TextField
                          label="Nombre de la etapa"
                          placeholder="Relevamiento en campo"
                          fullWidth
                          {...register(`workPlanStages.${index}.stageName` as const)}
                          error={!!errors.workPlanStages?.[index]?.stageName}
                          helperText={errors.workPlanStages?.[index]?.stageName?.message}
                        />
                        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
                          <TextField
                            label="Inicio"
                            type="date"
                            fullWidth
                            InputLabelProps={{ shrink: true }}
                            {...register(`workPlanStages.${index}.stageStart` as const)}
                            error={!!errors.workPlanStages?.[index]?.stageStart}
                            helperText={errors.workPlanStages?.[index]?.stageStart?.message}
                          />
                          <TextField
                            label="Fin"
                            type="date"
                            fullWidth
                            InputLabelProps={{ shrink: true }}
                            {...register(`workPlanStages.${index}.stageEnd` as const)}
                            error={!!errors.workPlanStages?.[index]?.stageEnd}
                            helperText={errors.workPlanStages?.[index]?.stageEnd?.message}
                          />
                        </Stack>
                      </Stack>
                      <Stack spacing={2}>
                        <TextField
                          select
                          label="Tipo de soporte requerido"
                          fullWidth
                          defaultValue={field.supportType}
                          {...register(`workPlanStages.${index}.supportType` as const)}
                        >
                          <MenuItem value="financial">Financiamiento</MenuItem>
                          <MenuItem value="materials">Materiales</MenuItem>
                          <MenuItem value="labor">Mano de obra</MenuItem>
                          <MenuItem value="logistics">Logística</MenuItem>
                          <MenuItem value="other">Otro</MenuItem>
                        </TextField>
                        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
                          <TextField
                            label="Monto estimado"
                            type="number"
                            inputProps={{ min: 0, step: 100 }}
                            fullWidth
                            {...register(`workPlanStages.${index}.estimatedAmount` as const, { valueAsNumber: true })}
                            error={!!errors.workPlanStages?.[index]?.estimatedAmount}
                            helperText={errors.workPlanStages?.[index]?.estimatedAmount?.message}
                          />
                          <TextField
                            label="Moneda del monto"
                            placeholder="USD"
                            inputProps={{ maxLength: 3 }}
                            fullWidth
                            {...register(`workPlanStages.${index}.amountCurrency` as const)}
                            error={!!errors.workPlanStages?.[index]?.amountCurrency}
                            helperText={errors.workPlanStages?.[index]?.amountCurrency?.message}
                          />
                        </Stack>
                      </Stack>
                      <TextField
                        label="Descripción del pedido"
                        placeholder="Detalle del recurso requerido, alcance y observaciones..."
                        fullWidth
                        multiline
                        minRows={3}
                        {...register(`workPlanStages.${index}.description` as const)}
                        error={!!errors.workPlanStages?.[index]?.description}
                        helperText={errors.workPlanStages?.[index]?.description?.message}
                      />
                    </Stack>
                  </Stack>
                </Paper>
              ))}
            </Stack>
          </Paper>

          <Stack direction={{ xs: 'column', sm: 'row' }} justifyContent="flex-end" spacing={2}>
            <Button 
              type="submit" 
              variant="contained" 
              startIcon={<Save />} 
              size="large" 
              disabled={isLoading}
              sx={{ width: { xs: '100%', sm: 'auto' } }}
            >
              {isLoading ? 'Enviando...' : 'Enviar a Bonita'}
            </Button>
          </Stack>
        </Stack>
      </Box>

      {lastResult && (
        <Box mt={4}>
          <Alert severity="success" variant="outlined">
            <Typography variant="subtitle1" fontWeight={600}>
              Proyecto enviado correctamente
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Case ID: <strong>{lastResult.caseId}</strong> · Process Definition: {lastResult.processDefinitionId}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Timestamp: {new Date(lastResult.createdAt).toLocaleString()}
            </Typography>
          </Alert>
        </Box>
      )}
    </Box>
  )
}
