# ProjectPlanning - Entrega 2

Aplicación full-stack (React + FastAPI + PostgreSQL + Bonita BPM) para la **Entrega 2** del Trabajo Práctico Integrador de _Desarrollo de Software en Sistemas Distribuidos (2025)_.

## Objetivo de la entrega

- Implementar el formulario web de alta de proyectos.
- Exponer un backend que reciba la información del formulario, la valide y cree la instancia del proceso en Bonita BPM cargando el volumen de datos (Business Data Model).
- Preparar la infraestructura dockerizada (frontend, backend, base de datos y Bonita).
- Documentar las variables de proceso requeridas en Bonita.

## Estructura del repositorio

```
.
├── backend/                # Código fuente del backend (FastAPI)
├── docs/                   # Documentación complementaria (p.ej. variables Bonita)
├── frontend/               # Aplicación web (React + TS + Vite)
├── infra/                  # Configuraciones de infraestructura (Docker, scripts)
├── scripts/                # Scripts auxiliares para automatizaciones
└── README.md               # Este archivo
```

## Stack tecnológico

- **Frontend**: React 19 + TypeScript + Vite, Material UI, React Hook Form, Zod, React Query, Axios.
- **Backend**: FastAPI (Python 3.11), SQLAlchemy, Auth JWT, integración Bonita vía REST, httpx.
- **Base de datos**: PostgreSQL.
- **Orquestación**: Docker & docker-compose.
- **Tests**: Vitest + Testing Library (frontend), Pytest + coverage (backend).

## Requisitos previos

- Node.js >= 20
- Python >= 3.11
- Docker & Docker Compose
- Bonita BPM 7.9.0 o superior (se utilizará imagen docker oficial).

## Variables de entorno

| Servicio  | Archivo                   | Descripción                                   |
|-----------|---------------------------|-----------------------------------------------|
| Frontend  | `frontend/.env.example`   | URL base de la API                            |
| Backend   | `backend/.env.example`    | Config DB, JWT y credenciales Bonita          |
| Infra     | `infra/.env.example`      | Variables compartidas para docker-compose     |

Copiar cada `*.env.example` a `.env` y ajustar valores.

## Puesta en marcha (Docker)

Esta aplicación está configurada para dos entornos: desarrollo (con hot-reloading) y producción.

### Entorno de Desarrollo

**Prerequisito**: Bonita BPM debe estar corriendo localmente en puerto 8080.

Para levantar el entorno de desarrollo, que incluye hot-reloading para el frontend y el backend, ejecuta:

```bash
./scripts/start-dev.sh
```

Esto usará el archivo `infra/docker-compose.dev.yml`.

Servicios expuestos en desarrollo:

- Frontend (Vite): <http://localhost:5173>
- Backend API (FastAPI): <http://localhost:8000/api/v1>
- Swagger Backend: <http://localhost:8000/docs>
- Bonita BPM Portal: <http://localhost:8080/bonita> (LOCAL - no en Docker)
- PostgreSQL: `localhost:5432`

### Entorno de Producción

Para simular el entorno de producción (sin hot-reloading), puedes usar:

```bash
docker-compose -f infra/docker-compose.prod.yml up --build
```

## Pruebas

- Frontend: `cd frontend && npm run test`
- Backend: `cd backend && pytest`

## Variables de proceso Bonita

La documentación completa se encuentra en [`docs/bonita-variables.md`](docs/bonita-variables.md), incluyendo:

- Definición del Business Data Model (`Project`, `WorkPlanStage`).
- Variables de contrato para la tarea de inicio.
- Notas sobre carga de datos y relaciones.