import { describe, it, expect } from 'vitest'
import { projectSchema, workPlanStageSchema } from './validation'

describe('workPlanStageSchema', () => {
  it('should validate valid stage data', () => {
    const validStage = {
      stageName: 'Preparación del terreno',
      stageStart: '2025-01-15',
      stageEnd: '2025-01-30',
      supportType: 'labor' as const,
      description: 'Limpiar y preparar el área de construcción',
      estimatedAmount: 5000,
      amountCurrency: 'USD',
    }

    const result = workPlanStageSchema.safeParse(validStage)
    expect(result.success).toBe(true)
    expect(result.data?.amountCurrency).toBe('USD')
  })

  it('should reject stage with invalid date range', () => {
    const invalidStage = {
      stageName: 'Etapa inválida',
      stageStart: '2025-01-30',
      stageEnd: '2025-01-15',
      supportType: 'financial' as const,
      description: 'Descripción de prueba',
    }

    const result = workPlanStageSchema.safeParse(invalidStage)
    expect(result.success).toBe(false)
    if (!result.success) {
      expect(result.error.issues).toEqual(
        expect.arrayContaining([
          expect.objectContaining({
            path: ['stageEnd'],
            message: 'La fecha fin debe ser posterior a la fecha de inicio',
          }),
        ])
      )
    }
  })

  it('should handle optional fields correctly', () => {
    const minimalStage = {
      stageName: 'Etapa básica',
      stageStart: '2025-01-15',
      stageEnd: '2025-01-30',
      supportType: 'materials' as const,
      description: 'Descripción mínima requerida',
    }

    const result = workPlanStageSchema.safeParse(minimalStage)
    expect(result.success).toBe(true)
    expect(result.data?.estimatedAmount).toBeUndefined()
    expect(result.data?.amountCurrency).toBeUndefined()
  })
})

describe('projectSchema', () => {
  it('should validate complete project data', () => {
    const validProject = {
      projectName: 'Mejora habitacional rural',
      projectDescription: 'Proyecto para mejorar las condiciones de vivienda en comunidades rurales mediante la construcción de sistemas sanitarios y mejoras estructurales.',
      projectCategory: 'Infraestructura',
      requestingOrganization: 'ONG Esperanza Rural',
      contactEmail: 'contacto@esperanzarural.org',
      contactPhone: '+54 11 4555-1234',
      estimatedBudget: 150000,
      currency: 'ARS',
      startDate: '2025-02-01',
      endDate: '2025-08-31',
      priorityLevel: 'high' as const,
      supportingDocsUrl: 'https://drive.google.com/folder/abc123',
      workPlanStages: [
        {
          stageName: 'Relevamiento inicial',
          stageStart: '2025-02-01',
          stageEnd: '2025-02-15',
          supportType: 'labor' as const,
          description: 'Evaluación técnica y social del área de trabajo',
          estimatedAmount: 10000,
          amountCurrency: 'ARS',
        },
      ],
    }

    const result = projectSchema.safeParse(validProject)
    expect(result.success).toBe(true)
    expect(result.data?.currency).toBe('ARS')
    expect(result.data?.workPlanStages).toHaveLength(1)
  })

  it('should reject project with invalid date range', () => {
    const invalidProject = {
      projectName: 'Proyecto con fechas incorrectas',
      projectDescription: 'Descripción suficientemente larga para cumplir validación.',
      projectCategory: 'Test',
      requestingOrganization: 'ONG Test',
      contactEmail: 'test@example.org',
      estimatedBudget: 1000,
      currency: 'USD',
      startDate: '2025-08-31',
      endDate: '2025-02-01',
      priorityLevel: 'medium' as const,
      workPlanStages: [
        {
          stageName: 'Etapa',
          stageStart: '2025-03-01',
          stageEnd: '2025-03-15',
          supportType: 'financial' as const,
          description: 'Descripción válida',
        },
      ],
    }

    const result = projectSchema.safeParse(invalidProject)
    expect(result.success).toBe(false)
    if (!result.success) {
      expect(result.error.issues).toEqual(
        expect.arrayContaining([
          expect.objectContaining({
            path: ['endDate'],
            message: 'La fecha fin debe ser posterior a la fecha de inicio',
          }),
        ])
      )
    }
  })

  it('should transform currency fields to uppercase', () => {
    const projectWithLowerCurrency = {
      projectName: 'Test project',
      projectDescription: 'Una descripción válida y suficientemente larga para pasar validación.',
      projectCategory: 'Test',
      requestingOrganization: 'ONG Test',
      contactEmail: 'test@example.org',
      estimatedBudget: 1000,
      currency: 'usd',
      startDate: '2025-01-01',
      endDate: '2025-12-31',
      priorityLevel: 'low' as const,
      workPlanStages: [
        {
          stageName: 'Stage',
          stageStart: '2025-01-01',
          stageEnd: '2025-01-15',
          supportType: 'financial' as const,
          description: 'Valid description',
          amountCurrency: 'eur',
        },
      ],
    }

    const result = projectSchema.safeParse(projectWithLowerCurrency)
    expect(result.success).toBe(true)
    expect(result.data?.currency).toBe('USD')
    expect(result.data?.workPlanStages[0]?.amountCurrency).toBe('EUR')
  })

  it('should handle empty optional fields', () => {
    const projectWithEmptyOptionals = {
      projectName: 'Minimal project',
      projectDescription: 'Descripción mínima válida para cumplir requisitos.',
      projectCategory: 'Test',
      requestingOrganization: 'ONG Test',
      contactEmail: 'test@example.org',
      contactPhone: '',
      estimatedBudget: 1000,
      currency: 'USD',
      startDate: '2025-01-01',
      endDate: '2025-12-31',
      priorityLevel: 'medium' as const,
      supportingDocsUrl: '',
      workPlanStages: [
        {
          stageName: 'Single stage',
          stageStart: '2025-01-01',
          stageEnd: '2025-01-15',
          supportType: 'other' as const,
          description: 'Basic stage description',
        },
      ],
    }

    const result = projectSchema.safeParse(projectWithEmptyOptionals)
    expect(result.success).toBe(true)
    expect(result.data?.contactPhone).toBeUndefined()
    expect(result.data?.supportingDocsUrl).toBeUndefined()
  })
})
