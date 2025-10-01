import { z } from 'zod'
import { isBefore, parseISO } from 'date-fns'

const optionalCurrencySchema = z
  .string()
  .trim()
  .optional()
  .transform((value) => (value ? value.toUpperCase() : undefined))
  .refine((value) => value === undefined || value.length === 3, {
    message: 'Debe contener 3 letras (ISO-4217)',
  })

const optionalPositiveNumberSchema = z
  .union([z.string(), z.number(), z.null(), z.undefined()])
  .transform((value) => {
    if (value === '' || value === null || value === undefined) {
      return undefined
    }
    const numeric = typeof value === 'number' ? value : Number(value)
    return Number.isNaN(numeric) ? NaN : numeric
  })
  .refine((value) => value === undefined || !Number.isNaN(value), {
    message: 'Debe ser un número válido',
  })
  .refine((value) => value === undefined || value >= 0, {
    message: 'Debe ser un número positivo',
  })

const positiveNumberSchema = z
  .coerce.number()
  .refine((value) => !Number.isNaN(value), { message: 'Debe ser un número válido' })
  .refine((value) => value >= 0, { message: 'Debe ser positivo' })

const optionalStringSchema = z
  .string()
  .trim()
  .optional()
  .transform((value) => (value === '' ? undefined : value))

const validateDates = (start: string, end: string, ctx: z.RefinementCtx, startPath: (string | number)[], endPath: (string | number)[]) => {
  const parsedStart = parseISO(start)
  if (Number.isNaN(parsedStart.getTime())) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      path: startPath,
      message: 'Fecha inválida',
    })
  }

  const parsedEnd = parseISO(end)
  if (Number.isNaN(parsedEnd.getTime())) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      path: endPath,
      message: 'Fecha inválida',
    })
    return
  }

  if (!Number.isNaN(parsedStart.getTime()) && isBefore(parsedEnd, parsedStart)) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      path: endPath,
      message: 'La fecha fin debe ser posterior a la fecha de inicio',
    })
  }
}

export const workPlanStageSchema = z
  .object({
    stageName: z.string().min(3, 'El nombre debe tener al menos 3 caracteres'),
    stageStart: z.string().min(1, 'La fecha de inicio es requerida'),
    stageEnd: z.string().min(1, 'La fecha de fin es requerida'),
    supportType: z.enum(['financial', 'materials', 'labor', 'logistics', 'other']),
    description: z.string().min(5, 'La descripción debe tener al menos 5 caracteres'),
    estimatedAmount: optionalPositiveNumberSchema,
    amountCurrency: optionalCurrencySchema,
  })
  .superRefine((data, ctx) => {
    validateDates(data.stageStart, data.stageEnd, ctx, ['stageStart'], ['stageEnd'])
  })

export const projectSchema = z
  .object({
    projectName: z.string().min(5, 'El nombre debe tener al menos 5 caracteres'),
    projectDescription: z.string().min(20, 'La descripción debe tener al menos 20 caracteres'),
    projectCategory: z.string().min(3, 'La categoría debe tener al menos 3 caracteres'),
    requestingOrganization: z.string().min(3, 'La organización debe tener al menos 3 caracteres'),
    contactEmail: z.string().email('Email inválido'),
    contactPhone: optionalStringSchema.refine(
      (value) => value === undefined || (value.length >= 6 && value.length <= 30),
      {
        message: 'El teléfono debe tener entre 6 y 30 caracteres',
      },
    ),
    estimatedBudget: positiveNumberSchema,
    currency: z
      .string()
      .trim()
      .length(3, 'Debe contener 3 letras (ISO-4217)')
      .transform((value) => value.toUpperCase()),
    startDate: z.string().min(1, 'La fecha de inicio es requerida'),
    endDate: z.string().min(1, 'La fecha de fin es requerida'),
    priorityLevel: z.enum(['low', 'medium', 'high', 'critical']),
    supportingDocsUrl: optionalStringSchema.refine(
      (value) => value === undefined || /^https?:\/\/.+/i.test(value),
      {
        message: 'Debe ser una URL válida',
      },
    ),
    workPlanStages: z.array(workPlanStageSchema).min(1, 'Debe cargar al menos una etapa'),
  })
  .superRefine((data, ctx) => {
    validateDates(data.startDate, data.endDate, ctx, ['startDate'], ['endDate'])
  })
  
export type ProjectSchema = z.infer<typeof projectSchema>
