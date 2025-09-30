# Variables de Proceso y Business Data Model – ProjectPlanning

Este documento describe las variables que deben configurarse en Bonita BPM para la instancia del proceso **ProjectPlanning** y el Business Data Model (BDM) que almacenará el volumen de datos del proyecto.

## 1. Business Data Model

Se debe crear dos entidades principales con la siguiente estructura:

### 1.1. `Project`

| Campo                  | Tipo Bonita | Descripción                                                                 |
|------------------------|-------------|-----------------------------------------------------------------------------|
| `projectName`          | String      | Nombre del proyecto (longitud sugerida 150).                               |
| `projectDescription`   | Text        | Descripción detallada (hasta 2000 caracteres).                              |
| `projectCategory`      | String      | Categoría del proyecto (energía, infraestructura, etc.).                    |
| `requestingOrganization` | String   | Nombre de la ONG solicitante.                                               |
| `contactEmail`         | String      | Email de contacto del proyecto.                                            |
| `contactPhone`         | String      | Teléfono de contacto (opcional).                                           |
| `estimatedBudget`      | Double      | Presupuesto estimado.                                                      |
| `currency`             | String      | Código ISO-4217 (ej. ARS, USD).                                            |
| `startDate`            | Date        | Fecha estimada de inicio.                                                  |
| `endDate`              | Date        | Fecha estimada de finalización.                                            |
| `priorityLevel`        | String      | Prioridad: `low`, `medium`, `high`, `critical`.                            |
| `supportingDocsUrl`    | String      | URL a documentación adicional (opcional).                                  |
| `submissionTimestamp`  | DateTime    | Marca temporal de creación del caso.                                       |
| `initiatorUserId`      | String      | Usuario que inicia el proceso (email/login).                               |
| `workPlanStages`       | Relación 1..n con `WorkPlanStage`.                |

### 1.2. `WorkPlanStage`

| Campo             | Tipo Bonita | Descripción                                                             |
|-------------------|-------------|-------------------------------------------------------------------------|
| `stageName`       | String      | Nombre de la etapa.                                                    |
| `stageStart`      | Date        | Fecha de inicio estimada de la etapa.                                  |
| `stageEnd`        | Date        | Fecha estimada de finalización.                                        |
| `supportType`     | String      | Tipo de soporte requerido (`financial`, `materials`, `labor`, etc.).   |
| `description`     | Text        | Detalle del pedido.                                                    |
| `estimatedAmount` | Double      | Cantidad estimada (opcional).                                          |
| `amountCurrency`  | String      | Moneda asociada al monto (opcional).                                   |

Definir la relación `Project` (1) --- (n) `WorkPlanStage` como *composition* para que al crear el proyecto se persistan sus etapas.

## 2. Variables de Proceso (Contract Inputs)

El contrato de la tarea de inicio (Start Event) debe contener una única variable compuesta:

```
project (Type: complex)
├─ projectName (String)
├─ projectDescription (Text)
├─ projectCategory (String)
├─ requestingOrganization (String)
├─ contactEmail (String)
├─ contactPhone (String) [opcional]
├─ estimatedBudget (Double)
├─ currency (String)
├─ startDate (Date)
├─ endDate (Date)
├─ priorityLevel (String)
├─ supportingDocsUrl (String) [opcional]
├─ workPlanStages (List of complex)
│   ├─ stageName (String)
│   ├─ stageStart (Date)
│   ├─ stageEnd (Date)
│   ├─ supportType (String)
│   ├─ description (Text)
│   ├─ estimatedAmount (Double) [opcional]
│   └─ amountCurrency (String) [opcional]
├─ submissionTimestamp (DateTime)
└─ initiatorUserId (String)
```

### 2.1. Script de contrato → Business Data

En la operación del Start Event mapear el contrato hacia el BDM, por ejemplo:

```groovy
import com.projectplanning.Project
import com.projectplanning.WorkPlanStage

Project project = new Project()
project.projectName = projectInput.projectName
project.projectDescription = projectInput.projectDescription
project.projectCategory = projectInput.projectCategory
project.requestingOrganization = projectInput.requestingOrganization
project.contactEmail = projectInput.contactEmail
project.contactPhone = projectInput.contactPhone
project.estimatedBudget = projectInput.estimatedBudget
project.currency = projectInput.currency
project.startDate = projectInput.startDate
project.endDate = projectInput.endDate
project.priorityLevel = projectInput.priorityLevel
project.supportingDocsUrl = projectInput.supportingDocsUrl
project.submissionTimestamp = projectInput.submissionTimestamp
project.initiatorUserId = projectInput.initiatorUserId

project.workPlanStages = projectInput.workPlanStages.collect { stageInput ->
    WorkPlanStage stage = new WorkPlanStage()
    stage.stageName = stageInput.stageName
    stage.stageStart = stageInput.stageStart
    stage.stageEnd = stageInput.stageEnd
    stage.supportType = stageInput.supportType
    stage.description = stageInput.description
    stage.estimatedAmount = stageInput.estimatedAmount
    stage.amountCurrency = stageInput.amountCurrency
    stage
}

return project
```

Asignar el resultado a la variable de proceso (business data) `project`.

## 3. Configuración del Proceso en Bonita

1. **Crear/Importar el BDM**: desde *Development > Business Data Model*.
2. **Configurar el contrato** del Start Event con la estructura descrita.
3. **Definir la operación** que asigna el contrato a la business data `project`.
4. **Publicar el BDM** y sincronizar antes de ejecutar el proceso.
5. **Registrar usuarios técnicos**: el backend se autenticará con un usuario técnico (`technical_user`) para invocar la API REST.

## 4. Variables utilizadas por el Backend

El backend envía al contrato los campos anteriores y utiliza la siguiente metadata adicional:

- `submissionTimestamp`: se setea con el timestamp actual (UTC).
- `initiatorUserId`: corresponde al email/login del usuario autenticado en la aplicación web.
- `workPlanStages`: lista de etapas ingresadas desde el formulario.

## 5. Consideraciones adicionales

- Validar que las fechas sean coherentes (`stageStart >= startDate`, `stageEnd <= endDate`, etc.) del lado de Bonita o de la aplicación.
- La lista de `workPlanStages` puede acotarse a 20 elementos para la entrega actual.
- Si se requieren archivos adjuntos, considerar almacenar URLs firmadas (S3, Drive, etc.) y registrarlas en `supportingDocsUrl`.

Con esta configuración, el backend podrá iniciar instancias del proceso en Bonita con el volumen de datos necesario para las etapas siguientes.
