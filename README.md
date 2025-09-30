# ProjectPlanning - Entrega 2

Aplicación full-stack (React + FastAPI + PostgreSQL + Bonita BPM) para la **Entrega 2** del Trabajo Práctico Integrador de _Desarrollo de Software en Sistemas Distribuidos (2025)_.

## Objetivo de la entrega

- Implementar el formulario web de alta de proyectos.
- Exponer un backend que reciba la información del formulario, la valide y cree la instancia del proceso en Bonita BPM cargando el volumen de datos (Business Data Model).
- Preparar la infraestructura dockerizada (frontend, backend, base de datos y Bonita).
- Incluir pruebas unitarias básicas en frontend y backend.
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

## Puesta en marcha local (Docker + Bonita local)

**Prerequisito**: Bonita BPM debe estar corriendo localmente en puerto 8080.

```bash
# Iniciar Bonita localmente primero
# Luego ejecutar el stack Docker:
docker compose -f infra/docker-compose.yml up --build
```

Servicios expuestos:

- Frontend: <http://localhost:5173>
- Backend API: <http://localhost:8000/api/v1>
- Swagger Backend: <http://localhost:8000/docs>
- Bonita BPM Portal: <http://localhost:8080/bonita> (LOCAL - no en Docker)
- PostgreSQL: `localhost:5432` (usuario/clave definidas en `.env`)

## Desarrollo local sin Docker

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .[test]
uvicorn app.main:app --reload
```

## Pruebas

- Frontend: `cd frontend && npm run test`
- Backend: `cd backend && pytest`

## Variables de proceso Bonita

La documentación completa se encuentra en [`docs/bonita-variables.md`](docs/bonita-variables.md), incluyendo:

- Definición del Business Data Model (`Project`, `WorkPlanStage`).
- Variables de contrato para la tarea de inicio.
- Notas sobre carga de datos y relaciones.

## Próximos pasos

1. Implementar formulario y lógica de envío en el frontend.
2. Exponer endpoints en backend y conexión con Bonita.
3. Añadir pruebas unitarias.
4. Completar configuración docker-compose.
5. Actualizar documentación e instrucciones finales.

---
Cualquier duda o ajuste necesario quedará documentado en los próximos commits y en los archivos de la carpeta `docs/`.
# dssd-2025
# dssd-2025
# dssd-2025
