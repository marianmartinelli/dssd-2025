from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, TYPE_CHECKING, List

import httpx
from fastapi import HTTPException, status
from structlog import get_logger

from app.core.config import get_settings
from app.schemas.project import ProjectCreate, WorkPlanStage, ObservationCreate
from app.schemas.metrics import BonitaCompletedCase
from app.services.bonita_session_manager import BonitaSession

if TYPE_CHECKING:
    from app.models.project import Project

logger = get_logger()
settings = get_settings()


class BonitaClient:
    """Cliente para interactuar con Bonita BPM usando una sesión autenticada."""

    def __init__(self, session: BonitaSession) -> None:
        """
        Inicializa el cliente con una sesión autenticada de Bonita.

        Args:
            session: Sesión de Bonita autenticada con las credenciales del usuario
        """
        self.session = session
        if not session.is_authenticated:
            raise ValueError("La sesión de Bonita debe estar autenticada antes de crear el cliente")

    async def _get_process_definition_id(self) -> str:
        """Obtiene el ID de la definición del proceso de Bonita."""
        params = {
            "f": [f"name={settings.bonita_process_definition}", f"version={settings.bonita_process_version}"],
        }
        response = await self.session.client.get(
            "/bonita/API/bpm/process",
            params=params,
            headers=self.session.auth_headers
        )
        response.raise_for_status()

        data = response.json()
        if not data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bonita process definition not found")

        return data[0]["id"]

    async def _get_observation_process_definition_id(self) -> str:
        """Obtiene el ID de la definición del proceso de observaciones de Bonita."""
        params = {
            "f": [f"name={settings.bonita_observation_process_definition}", f"version={settings.bonita_observation_process_version}"],
        }
        response = await self.session.client.get(
            "/bonita/API/bpm/process",
            params=params,
            headers=self.session.auth_headers
        )
        response.raise_for_status()

        data = response.json()
        if not data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bonita observation process definition not found")

        return data[0]["id"]

    async def instantiate_process(self, project: ProjectCreate, initiator_username: str) -> Dict[str, Any]:
        """Instancia un proceso de Bonita con los datos del proyecto."""
        process_id = await self._get_process_definition_id()

        contract_payload = self._build_contract_payload(project, initiator_username)
        response = await self.session.client.post(
            f"/bonita/API/bpm/process/{process_id}/instantiation",
            headers=self.session.auth_headers,
            content=json.dumps(contract_payload),
        )

        if response.status_code not in (status.HTTP_200_OK, status.HTTP_201_CREATED):
            logger.error(
                "Bonita instantiation failed",
                status_code=response.status_code,
                headers=dict(response.headers),
                body=response.text,
                payload=contract_payload,
            )
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Bonita process instantiation failed")

        response_data = response.json()
        response_data["processDefinitionId"] = process_id
        return response_data

    async def instantiate_observation_process(self, observation: "ObservationCreate", initiator_username: str) -> Dict[str, Any]:
        """Instancia un proceso de observación en Bonita con los datos de la observación."""
        # Obtener el process_id específico para observaciones (proceso separado)
        process_id = await self._get_observation_process_definition_id()

        contract_payload = self._build_observation_contract_payload(observation, initiator_username)
        response = await self.session.client.post(
            f"/bonita/API/bpm/process/{process_id}/instantiation",
            headers=self.session.auth_headers,
            content=json.dumps(contract_payload),
        )

        if response.status_code not in (status.HTTP_200_OK, status.HTTP_201_CREATED):
            logger.error(
                "Bonita observation instantiation failed",
                status_code=response.status_code,
                headers=dict(response.headers),
                body=response.text,
                payload=contract_payload,
            )
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Bonita observation process instantiation failed")

        response_data = response.json()
        response_data["processDefinitionId"] = process_id
        return response_data

    def _build_contract_payload(self, project: ProjectCreate, initiator_username: str) -> Dict[str, Any]:
        return {
            "proyectoContrato": {
                "projectName": project.project_name,
                "projectDescription": project.project_description,
                "projectCategory": project.project_category,
                "requestingOrganization": project.requesting_organization,
                "contactEmail": project.contact_email,
                "contactPhone": project.contact_phone,
                "estimatedBudget": project.estimated_budget,
                "currency": project.currency,
                "startDate": project.start_date.isoformat(),
                "endDate": project.end_date.isoformat(),
                "priorityLevel": project.priority_level,
                "supportingDocsUrl": project.supporting_docs_url,
                "workPlanStages": [self._map_stage(stage) for stage in project.work_plan_stages],
                "submissionTimestamp": project.start_date.strftime("%Y-%m-%dT00:00:00Z"),
                "initiatorUserId": initiator_username,
            }
        }

    def _map_stage(self, stage: WorkPlanStage) -> Dict[str, Any]:
        return {
            "stageName": stage.stage_name,
            "stageStart": stage.stage_start.isoformat(),
            "stageEnd": stage.stage_end.isoformat(),
            "supportType": stage.support_type,
            "description": stage.description,
            "estimatedAmount": stage.estimated_amount,
            "amountCurrency": stage.amount_currency,
        }

    def _build_observation_contract_payload(self, observation: "ObservationCreate", initiator_username: str) -> Dict[str, Any]:
        """Construye el payload del contrato para una observación."""
        from datetime import datetime
        return {
            "observacionContrato": {
                "project_id": observation.project_id,
                "title": observation.title,
                "description": observation.description or "",
                "created_date": datetime.utcnow().isoformat(),
                "created_by": initiator_username,
                "is_resolved": False,
            }
        }

    async def _get_task_by_case_id(self, case_id: str, max_retries: int = 10, retry_delay: float = 0.5) -> str:
        """Obtiene el taskId a partir del caseId con reintentos"""
        for attempt in range(max_retries):
            params = {"f": f"caseId={case_id}"}
            response = await self.session.client.get(
                "/bonita/API/bpm/userTask",
                params=params,
                headers=self.session.auth_headers
            )

            if response.status_code != status.HTTP_200_OK:
                logger.error(
                    "Failed to get task by case ID",
                    status_code=response.status_code,
                    case_id=case_id,
                    body=response.text,
                )
                raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed to get task from Bonita")

            data = response.json()
            if data:
                task_id = data[0]["id"]
                logger.info("Task retrieved", case_id=case_id, task_id=task_id, attempt=attempt + 1)
                return task_id

            # Se aplica un retardo antes del siguiente intento
            # Porque Bonita tarda en crear el HumanTask luego de instanciar el proceso
            if attempt < max_retries - 1:
                logger.info(
                    "No task found yet, retrying...",
                    case_id=case_id,
                    attempt=attempt + 1,
                    max_retries=max_retries,
                    retry_in_seconds=retry_delay,
                )
                await asyncio.sleep(retry_delay)

        # Si después de todos los reintentos no hay tarea
        logger.error("No task found after all retries", case_id=case_id, max_retries=max_retries)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No task found for case {case_id} after {max_retries} attempts",
        )

    async def get_task_by_case_and_name(
        self,
        case_id: str,
        task_name: str,
        max_retries: int = 10,
        retry_delay: float = 0.5
    ) -> str | None:
        """
        Obtiene el taskId a partir del caseId y nombre de tarea específico con reintentos.

        Args:
            case_id: El ID del caso en Bonita
            task_name: Nombre exacto de la tarea a buscar
            max_retries: Número máximo de reintentos
            retry_delay: Tiempo de espera entre reintentos

        Returns:
            El task ID si se encuentra, None si no existe después de todos los reintentos

        Raises:
            HTTPException: Si hay error de comunicación con Bonita
        """
        for attempt in range(max_retries):
            # First, get all tasks for this case to debug
            params_all = {"f": f"caseId={case_id}"}
            response_all = await self.session.client.get(
                "/bonita/API/bpm/userTask",
                params=params_all,
                headers=self.session.auth_headers
            )

            if response_all.status_code == status.HTTP_200_OK:
                all_tasks = response_all.json()
                logger.info(
                    "All tasks for case",
                    case_id=case_id,
                    tasks=[{"id": t.get("id"), "name": t.get("name"), "state": t.get("state")} for t in all_tasks]
                )

                # Find task by name in the results
                for task in all_tasks:
                    if task.get("name") == task_name:
                        task_id = task["id"]
                        logger.info(
                            "Task found by manual filtering",
                            case_id=case_id,
                            task_name=task_name,
                            task_id=task_id,
                            attempt=attempt + 1
                        )
                        return task_id

            # Se aplica un retardo antes del siguiente intento
            # Porque Bonita tarda en crear el HumanTask luego de completar la tarea anterior
            if attempt < max_retries - 1:
                logger.info(
                    "No task found yet, retrying...",
                    case_id=case_id,
                    task_name=task_name,
                    attempt=attempt + 1,
                    max_retries=max_retries,
                    retry_in_seconds=retry_delay,
                )
                await asyncio.sleep(retry_delay)

        # Si después de todos los reintentos no hay tarea, retornar None
        logger.warning(
            "No task found after all retries",
            case_id=case_id,
            task_name=task_name,
            max_retries=max_retries
        )
        return None

    async def _get_logged_user(self) -> str:
        """Obtiene el ID del usuario logueado en Bonita"""
        response = await self.session.client.get(
            "/bonita/API/system/session/1",
            headers=self.session.auth_headers
        )
        
        if response.status_code != status.HTTP_200_OK:
            logger.error(
                "Failed to get logged user session",
                status_code=response.status_code,
                body=response.text,
            )
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed to get user session from Bonita")

        data = response.json()
        user_id = data.get("user_id")
        
        if not user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User ID not found in session")

        logger.info("Logged user retrieved", user_id=user_id)
        return user_id

    async def assign_task_to_user(self, task_id: str, user_id: str) -> None:
        """Asigna una tarea a un usuario específico"""
        payload = {"assigned_id": user_id}
        response = await self.session.client.put(
            f"/bonita/API/bpm/userTask/{task_id}",
            headers=self.session.auth_headers,
            content=json.dumps(payload),
        )

        if response.status_code != status.HTTP_200_OK:
            logger.error(
                "Failed to assign task to user",
                status_code=response.status_code,
                task_id=task_id,
                user_id=user_id,
                body=response.text,
            )
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed to assign task in Bonita")

        logger.info("Task assigned to user", task_id=task_id, user_id=user_id)

    async def complete_task(self, task_id: str) -> None:
        """Marca una tarea como completada"""
        response = await self.session.client.post(
            f"/bonita/API/bpm/userTask/{task_id}/execution",
            headers=self.session.auth_headers,
        )

        if response.status_code not in (status.HTTP_200_OK, status.HTTP_204_NO_CONTENT):
            logger.error(
                "Failed to complete task",
                status_code=response.status_code,
                task_id=task_id,
                body=response.text,
            )
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed to complete task in Bonita")

        logger.info("Task completed", task_id=task_id)

    async def complete_task_with_contract(self, task_id: str, contract_data: Dict[str, Any]) -> None:
        """
        Completa una tarea en Bonita con datos de contrato.

        Args:
            task_id: ID de la tarea a completar
            contract_data: Diccionario con los datos del contrato

        Raises:
            HTTPException: Si falla la completación de la tarea
        """
        response = await self.session.client.post(
            f"/bonita/API/bpm/userTask/{task_id}/execution",
            headers=self.session.auth_headers,
            content=json.dumps(contract_data),
        )

        if response.status_code not in (status.HTTP_200_OK, status.HTTP_204_NO_CONTENT):
            logger.error(
                "Failed to complete task with contract",
                status_code=response.status_code,
                task_id=task_id,
                body=response.text,
                contract_keys=list(contract_data.keys()),
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to complete task in Bonita: {response.text}"
            )

        logger.info("Task completed with contract", task_id=task_id, contract_keys=list(contract_data.keys()))

    def build_project_update_contract(self, project: "Project") -> Dict[str, Any]:
        """
        Construye el payload del contrato para actualizaciones de proyecto.
        Incluye el proyecto completo con sus etapas y colaboraciones.

        Args:
            project: Objeto Project con relaciones cargadas (stages, collaborations)

        Returns:
            Diccionario con la estructura del contrato para Bonita
        """
        from app.models.user import User
        from sqlalchemy import select

        stages_data = []
        for stage in project.work_plan_stages:
            collaborations_data = []
            for collab in stage.collaboration_requests:
                # Get organization name if available
                org_name = "Particular"
                if collab.committed_by:
                    # Note: We'll need to pass this from the service layer
                    # or query it here if we have access to session
                    org_name = getattr(collab, "committed_by_organization", "Particular")

                collaborations_data.append({
                    "collaborationId": collab.id,
                    "title": collab.title,
                    "description": collab.description or "",
                    "requestedAmount": collab.requested_amount,
                    "amountCurrency": collab.amount_currency,
                    "requestedDate": collab.requested_date.isoformat() if collab.requested_date else "",
                    "isApproved": collab.is_approved,
                    "isCompleted": collab.is_completed,
                    "committedBy": collab.committed_by or "",
                    "committedByOrganization": org_name,
                })

            stages_data.append({
                "stageId": stage.id,
                "stageName": stage.stage_name,
                "stageStart": stage.stage_start.isoformat() if stage.stage_start else "",
                "stageEnd": stage.stage_end.isoformat() if stage.stage_end else "",
                "supportType": stage.support_type or "",
                "description": stage.description or "",
                "estimatedAmount": stage.estimated_amount,
                "amountCurrency": stage.amount_currency or "",
                "isCompleted": stage.is_completed,
                "collaborations": collaborations_data,
            })

        return {
            "projectUpdate": {
                "projectId": project.id,
                "caseId": project.case_id,
                "title": project.project_name,
                "description": project.project_description or "",
                "requestedAmount": project.estimated_budget,
                "amountCurrency": project.currency or "",
                "status": project.status,
                "initiatorUserId": project.initiator_user_id or "",
                "stages": stages_data,
            }
        }


async def instantiate_project(client: BonitaClient, project: ProjectCreate, initiator_username: str) -> Dict[str, Any]:
    """
    Instancia un proyecto en Bonita usando un cliente autenticado.

    Args:
        client: Cliente de Bonita ya autenticado con las credenciales del usuario
        project: Datos del proyecto a crear
        initiator_username: Username del usuario que inicia el proceso

    Returns:
        Diccionario con caseId y processDefinitionId

    Raises:
        HTTPException: Si ocurre algún error durante el proceso
    """
    try:
        response = await client.instantiate_process(project, initiator_username)

        if not response.get("caseId"):
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Case ID not found in Bonita response")

        logger.info("Bonita case created", response=response)
        case_id = response.get("caseId")
        processDefinitionId = response.get("processDefinitionId")

        task_id = await client._get_task_by_case_id(case_id)
        logger.info("Task ID obtained", task_id=task_id)

        user_id = await client._get_logged_user()
        logger.info("User ID obtained", user_id=user_id)

        await client.assign_task_to_user(task_id, user_id)
        logger.info("Task assigned successfully")

        await client.complete_task(task_id)
        logger.info("Task completed successfully")

        return {
            "caseId": case_id,
            "processDefinitionId": processDefinitionId,
        }
    except HTTPException as http_exc:
        logger.error("HTTP error in instantiate_project", status_code=http_exc.status_code, detail=http_exc.detail)
        raise
    except Exception as e:
        logger.error("Unexpected error in instantiate_project", error=str(e), error_type=type(e).__name__)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing project workflow: {str(e)}"
        )



async def instantiate_observation(client: BonitaClient, observation: ObservationCreate, initiator_username: str) -> Dict[str, Any]:
    """
    Instancia una observación en Bonita usando un cliente autenticado.
    Crea el caso, obtiene la tarea y la asigna al usuario, pero NO la completa.
    La tarea se completará cuando se resuelva la observación.

    Args:
        client: Cliente de Bonita ya autenticado con las credenciales del usuario
        observation: Datos de la observación a crear
        initiator_username: Username del usuario que inicia el proceso

    Returns:
        Diccionario con caseId, processDefinitionId y taskId

    Raises:
        HTTPException: Si ocurre algún error durante el proceso
    """
    try:
        # Instanciar el proceso de observación en Bonita
        response = await client.instantiate_observation_process(observation, initiator_username)

        if not response.get("caseId"):
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Case ID not found in Bonita response")

        logger.info("Bonita observation case created", response=response)
        case_id = response.get("caseId")
        processDefinitionId = response.get("processDefinitionId")

        # Obtener y asignar la tarea inicial (pero NO completarla)
        task_id = await client._get_task_by_case_id(case_id)
        logger.info("Task ID obtained for observation", task_id=task_id)

        user_id = await client._get_logged_user()
        logger.info("User ID obtained", user_id=user_id)

        await client.assign_task_to_user(task_id, user_id)
        logger.info("Observation task assigned successfully (not completed yet)")

        return {
            "caseId": case_id,
            "processDefinitionId": processDefinitionId,
            "taskId": task_id,
        }
    except HTTPException as http_exc:
        logger.error("HTTP error in instantiate_observation", status_code=http_exc.status_code, detail=http_exc.detail)
        raise
    except Exception as e:
        logger.error("Unexpected error in instantiate_observation", error=str(e), error_type=type(e).__name__)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing observation workflow: {str(e)}"
        )


async def advance_project_in_bonita(
    client: BonitaClient,
    project: "Project",
    expected_task_name: str,
    initiator_username: str
) -> Dict[str, Any]:
    """
    Avanza un proyecto a la siguiente etapa del proceso Bonita.

    Pasos:
    1. Busca la tarea actual por case_id y nombre esperado
    2. Asigna la tarea al usuario logueado
    3. Construye el contrato con el estado completo del proyecto
    4. Completa la tarea con el contrato

    Args:
        client: Cliente de Bonita autenticado
        project: Proyecto con todas sus relaciones cargadas
        expected_task_name: Nombre de la tarea que esperamos encontrar
        initiator_username: Username del usuario que ejecuta la acción

    Returns:
        Dict con taskId completado y información de la transición

    Raises:
        HTTPException: Si no se encuentra la tarea o falla la completación
    """
    if not project.case_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project does not have a Bonita case ID"
        )

    try:
        # First, get all current tasks to see what's actually available
        params_all = {"f": f"caseId={project.case_id}"}
        response_all = await client.session.client.get(
            "/bonita/API/bpm/userTask",
            params=params_all,
            headers=client.session.auth_headers
        )

        current_tasks = []
        if response_all.status_code == status.HTTP_200_OK:
            current_tasks = response_all.json()
            logger.info(
                "Current tasks in Bonita before advancing",
                case_id=project.case_id,
                expected_task=expected_task_name,
                current_tasks=[{"id": t.get("id"), "name": t.get("name"), "state": t.get("state")} for t in current_tasks],
                project_id=project.id
            )

        # 1. Buscar la tarea por caso y nombre
        task_id = await client.get_task_by_case_and_name(
            case_id=str(project.case_id),
            task_name=expected_task_name
        )

        if not task_id:
            # Log what tasks ARE available
            available_task_names = [t.get("name") for t in current_tasks] if current_tasks else []
            logger.warning(
                "Expected task not found in Bonita",
                case_id=project.case_id,
                expected_task=expected_task_name,
                available_tasks=available_task_names,
                project_id=project.id
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task '{expected_task_name}' not found for case {project.case_id}. Available tasks: {available_task_names}"
            )

        logger.info(
            "Task found in Bonita",
            task_id=task_id,
            task_name=expected_task_name,
            case_id=project.case_id,
            project_id=project.id
        )

        # 2. Asignar tarea al usuario actual
        user_id = await client._get_logged_user()
        await client.assign_task_to_user(task_id, user_id)

        # 3. Construir contrato con el estado completo del proyecto
        contract_data = client.build_project_update_contract(project)

        # 4. Completar la tarea con el contrato
        await client.complete_task_with_contract(task_id, contract_data)

        logger.info(
            "Project advanced in Bonita successfully",
            task_id=task_id,
            task_name=expected_task_name,
            project_id=project.id,
            case_id=project.case_id,
            new_status=project.status
        )

        return {
            "task_id": task_id,
            "task_name": expected_task_name,
            "case_id": project.case_id,
            "project_id": project.id,
        }

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(
            "Unexpected error advancing project in Bonita",
            error=str(e),
            error_type=type(e).__name__,
            task_name=expected_task_name,
            project_id=project.id,
            case_id=project.case_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error advancing project in Bonita: {str(e)}"
        )

async def get_completed_cases(self) -> List[Dict[str, Any]]:
    """
    Obtiene todos los cases completados de Bonita.
    Retorna una lista de dicts con caseId y endDate.
    
    Query Bonita: GET /bonita/API/bpm/case?f=state=completed&c=1000
    """
    try:
        # Parámetros comunes para ambas queries
        params = {
            #"f": "state=archived",  # filtro: solo cases completados
            "c": 1000,  # limit: máximo 1000 resultados
            "p": 0,  # page: comenzar desde página 0
        }

        params_arch = {
            "p": 0,  # page: comenzar desde página 0
        }

        # 1. Obtener casos completados activos
        response_active = await self.session.client.get(
            "/bonita/API/bpm/archivedcase",
            params=params,
            headers=self.session.auth_headers,
        )
        response_active.raise_for_status()
        active_cases = response_active.json() if isinstance(response_active.json(), list) else []

        logger.info("Active completed cases retrieved from Bonita", count=len(active_cases))

        # 2. Obtener casos completados archivados
        #response_archived = await self.session.client.get(
        #    "/bonita/API/bpm/archivedcase",
        #    params=params_arch,
        #    headers=self.session.auth_headers,
        #)
        #response_archived.raise_for_status()
        #archived_cases = response_archived.json() if isinstance(response_archived.json(), list) else []

        #logger.info("Archived completed cases retrieved from Bonita", count=len(archived_cases))

        # 3. Procesar ambos listados
        #all_cases = active_cases + archived_cases

        cases_data = active_cases
        completed_cases: List[Dict[str, Any]] = []

        if isinstance(cases_data, list):
            for case in cases_data:
                case_id = case.get("id") or case.get("caseId")
                logger.debug("Processing case", case_id=case_id)
                # Intentar extraer end_date de varios campos posibles
                end_date_str = (
                    case.get("endDate")
                    or case.get("end_date")
                    or case.get("endDateString")
                    or case.get("completionDate")
                )
                
                end_date = None
                if end_date_str:
                    try:
                        # Parsear ISO format
                        from datetime import datetime
                        end_date = datetime.fromisoformat(
                            end_date_str.replace("Z", "+00:00")
                        )
                    except (ValueError, AttributeError):
                        # Si falla el parseo, dejar como None
                        pass

                if case_id:
                    completed_cases.append({
                        "caseId": int(case_id),
                        "endDate": end_date.isoformat() if end_date else None,
                    })

        logger.info("Completed cases retrieved from Bonita", count=len(completed_cases))
        return completed_cases

    except httpx.HTTPError as e:
        logger.error("Bonita request error retrieving completed cases", error=str(e))
        raise ValueError(f"Bonita request error: {str(e)}")
    except Exception as e:
        logger.error("Error retrieving completed cases from Bonita", error=str(e))
        raise ValueError(f"Error retrieving completed cases from Bonita: {str(e)}")

