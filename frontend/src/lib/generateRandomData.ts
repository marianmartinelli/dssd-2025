import type { ProjectFormValues, WorkPlanStageForm } from '../types/project'
import { addDays, addMonths, format } from 'date-fns'

const projectNames = [
  'Mejora de infraestructura comunitaria',
  'Sistema de energía solar para escuelas rurales',
  'Centro de salud móvil regional',
  'Programa de capacitación en oficios',
  'Red de agua potable comunitaria',
  'Huerta orgánica colectiva',
  'Biblioteca digital para jóvenes',
  'Centro de reciclaje municipal',
  'Desarrollo de microemprendimientos locales',
  'Refacción de espacios públicos',
]

const categories = [
  'Infraestructura',
  'Energía',
  'Salud',
  'Educación',
  'Agua y Saneamiento',
  'Agricultura',
  'Tecnología',
  'Medio Ambiente',
  'Economía Social',
  'Cultura',
]

const organizations = [
  'ONG Hope Builders',
  'Fundación Solidaridad',
  'Asociación Comunitaria del Sur',
  'Red de Desarrollo Local',
  'Cooperativa Manos Unidas',
  'Grupo de Acción Social',
  'Fundación Futuro Sustentable',
  'Colectivo de Ayuda Mutua',
  'ONG Caminos de Progreso',
  'Fundación Horizonte',
]

const stageNames = [
  'Relevamiento en campo',
  'Diseño y planificación',
  'Adquisición de materiales',
  'Ejecución de obra',
  'Capacitación del equipo',
  'Implementación piloto',
  'Evaluación y ajustes',
  'Despliegue final',
  'Monitoreo y seguimiento',
  'Documentación y cierre',
]

const descriptions = [
  'Este proyecto busca mejorar las condiciones de vida de la comunidad mediante intervenciones estratégicas y sostenibles.',
  'Iniciativa orientada a fortalecer capacidades locales y promover el desarrollo integral de la región beneficiaria.',
  'Propuesta de impacto social que incluye participación comunitaria activa y enfoque de derechos humanos.',
  'Proyecto de desarrollo comunitario con énfasis en inclusión social y generación de oportunidades.',
  'Intervención territorial que promueve la mejora de servicios básicos y calidad de vida de los habitantes.',
]

const stageDescriptions = [
  'Actividades de campo para relevamiento de necesidades y diagnóstico participativo con la comunidad.',
  'Desarrollo de planificación técnica detallada con cronograma de actividades y asignación de recursos.',
  'Gestión y adquisición de materiales e insumos necesarios para la ejecución según especificaciones técnicas.',
  'Implementación de las actividades principales del proyecto con supervisión técnica continua.',
  'Actividades de formación y capacitación del equipo técnico y beneficiarios directos del proyecto.',
]

const currencies = ['USD', 'EUR', 'ARS', 'BRL', 'CLP']
const priorityLevels: Array<'low' | 'medium' | 'high' | 'critical'> = ['low', 'medium', 'high', 'critical']
const supportTypes: Array<'financial' | 'materials' | 'labor' | 'logistics' | 'other'> = ['financial', 'materials', 'labor', 'logistics', 'other']

const randomElement = <T,>(array: readonly T[] | T[]): T => {
  return array[Math.floor(Math.random() * array.length)]
}

const randomInt = (min: number, max: number): number => {
  return Math.floor(Math.random() * (max - min + 1)) + min
}

const formatDateForInput = (date: Date): string => {
  return format(date, 'yyyy-MM-dd')
}

const generateRandomEmail = (orgName: string): string => {
  const domain = orgName
    .toLowerCase()
    .replace(/\s+/g, '')
    .replace(/[^a-z0-9]/g, '')
    .substring(0, 15)
  return `contacto@${domain}.org`
}

const generateRandomPhone = (): string => {
  const countryCode = randomElement(['+54', '+1', '+34', '+55', '+56'])
  const areaCode = randomInt(11, 99)
  const number = randomInt(1000, 9999)
  const extension = randomInt(1000, 9999)
  return `${countryCode} ${areaCode} ${number}-${extension}`
}

const generateRandomUrl = (): string | undefined => {
  if (Math.random() > 0.5) {
    return undefined
  }
  const id = Math.random().toString(36).substring(2, 15)
  return `https://drive.google.com/drive/folders/${id}`
}

export const generateRandomStage = (
  projectStart: Date,
  projectEnd: Date,
  stageIndex: number,
  totalStages: number,
  projectCurrency: string
): WorkPlanStageForm => {
  // Dividir el tiempo del proyecto en segmentos para las etapas
  const totalDays = Math.floor((projectEnd.getTime() - projectStart.getTime()) / (1000 * 60 * 60 * 24))
  const segmentDays = Math.floor(totalDays / totalStages)

  const stageStartDays = stageIndex * segmentDays
  const stageEndDays = Math.min((stageIndex + 1) * segmentDays, totalDays)

  const stageStart = addDays(projectStart, stageStartDays)
  const stageEnd = addDays(projectStart, stageEndDays)

  const supportType = randomElement(supportTypes)
  const hasAmount = Math.random() > 0.3

  return {
    stageName: randomElement(stageNames),
    stageStart: formatDateForInput(stageStart),
    stageEnd: formatDateForInput(stageEnd),
    supportType,
    description: randomElement(stageDescriptions),
    estimatedAmount: hasAmount ? randomInt(5000, 50000) : undefined,
    amountCurrency: hasAmount ? projectCurrency : undefined,
  }
}

export const generateRandomProjectData = (): ProjectFormValues => {
  const today = new Date()
  const startDate = addDays(today, randomInt(7, 180)) // Entre 1 semana y 6 meses
  const endDate = addMonths(startDate, randomInt(3, 24)) // Entre 3 y 24 meses después

  const currency = randomElement(currencies)
  const organization = randomElement(organizations)
  const numStages = randomInt(1, 4)

  const workPlanStages: WorkPlanStageForm[] = Array.from({ length: numStages }, (_, index) =>
    generateRandomStage(startDate, endDate, index, numStages, currency)
  )

  return {
    projectName: randomElement(projectNames),
    projectDescription: randomElement(descriptions),
    projectCategory: randomElement(categories),
    requestingOrganization: organization,
    contactEmail: generateRandomEmail(organization),
    contactPhone: generateRandomPhone(),
    estimatedBudget: randomInt(10000, 500000),
    currency,
    startDate: formatDateForInput(startDate),
    endDate: formatDateForInput(endDate),
    priorityLevel: randomElement(priorityLevels),
    supportingDocsUrl: generateRandomUrl(),
    workPlanStages,
  }
}
