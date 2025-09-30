# Configuración de Bonita BPM Local

Este documento describe cómo configurar y usar una instancia local de Bonita BPM en lugar del contenedor Docker.

## Requisitos

- Bonita BPM Community 7.15.0 o superior
- Java 11 o superior
- Puerto 8080 disponible

## Configuración del proyecto para Bonita local

El proyecto ya está configurado para usar Bonita local. Los cambios aplicados incluyen:

### 2. Variables de entorno
- `BONITA_BASE_URL=http://localhost:8080` en archivos `.env.example`
- Credenciales configurables para tu instancia local

### 3. Script de inicio
- `scripts/start-dev.sh` verifica que Bonita esté corriendo localmente
- Muestra advertencias si no detecta Bonita en puerto 8080

## Pasos para usar Bonita local

### 1. Iniciar Bonita BPM
```bash
# Desde tu instalación de Bonita
cd /path/to/bonita
./start-bonita.sh  # o start-bonita.bat en Windows
```

### 2. Configurar variables de entorno
```bash
# Copiar y editar archivos de configuración
cp backend/.env.example backend/.env
cp infra/.env.example infra/.env

# Editar backend/.env con tus credenciales reales:
BONITA_API_USERNAME=tu_usuario_tecnico
BONITA_API_PASSWORD=tu_password_tecnico
```

### 3. Configurar Business Data Model en Bonita

Seguir las instrucciones en `docs/bonita-variables.md` para:
- Crear entidades `Project` y `WorkPlanStage`
- Configurar contrato de inicio
- Crear usuario técnico para API REST

### 4. Iniciar el stack Docker
```bash
./scripts/start-dev.sh
```

## Verificación

1. **Bonita Portal**: http://localhost:8080/bonita
2. **Backend Health**: http://localhost:8000/health
3. **API Docs**: http://localhost:8000/docs
4. **Frontend**: http://localhost:5173

## Troubleshooting

### Error de conexión a Bonita
- Verificar que Bonita esté corriendo en puerto 8080
- Comprobar credenciales en `backend/.env`
- Revisar logs: `docker-compose logs backend`

### Error de autenticación
- Verificar que el usuario técnico exista en Bonita
- Comprobar permisos del usuario para crear procesos
- Revisar configuración del proceso `ProjectPlanningProcess`

### Error de Business Data Model
- Verificar que las entidades `Project` y `WorkPlanStage` estén desplegadas
- Comprobar que el contrato de inicio esté configurado correctamente
- Revisar que el proceso esté habilitado y desplegado
