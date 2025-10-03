from __future__ import annotations

import asyncio
import json
from typing import Any, Dict

import httpx
from fastapi import HTTPException, status
from structlog import get_logger

from app.core.config import get_settings
from app.schemas.project import ProjectCreate, WorkPlanStage

logger = get_logger()
settings = get_settings()


class BonitaClient:
    def __init__(self) -> None:
        self.base_url = settings.bonita_base_url
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=15.0)
        self._csrf_token: str | None = None

    async def _ensure_session(self) -> None:
        if self._csrf_token:
            return

        payload = {
            "username": settings.bonita_api_username,
            "password": settings.bonita_api_password,
            "redirect": "false",
        }

        response = await self._client.post("/bonita/loginservice", data=payload)
        if response.status_code != status.HTTP_204_NO_CONTENT:
            logger.error("Bonita login failed", status_code=response.status_code, body=response.text)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Bonita authentication failed",
            )

        self._csrf_token = self._client.cookies.get("X-Bonita-API-Token")
        if not self._csrf_token:
            logger.error("Bonita login failed: CSRF token not found in cookies")
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Bonita CSRF token not found")

        logger.info("Bonita session established")

    async def _get_process_definition_id(self) -> str:
        await self._ensure_session()

        params = {
            "f": [f"name={settings.bonita_process_definition}", f"version={settings.bonita_process_version}"],
        }
        response = await self._client.get("/bonita/API/bpm/process", params=params, headers=self._auth_headers)
        response.raise_for_status()

        data = response.json()
        if not data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bonita process definition not found")

        return data[0]["id"]

    @property
    def _auth_headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {
            "Content-Type": "application/json",
        }
        if self._csrf_token:
            headers["X-Bonita-API-Token"] = self._csrf_token
        return headers

    async def instantiate_process(self, project: ProjectCreate, initiator_username: str) -> Dict[str, Any]:
        process_id = await self._get_process_definition_id()

        contract_payload = self._build_contract_payload(project, initiator_username)
        response = await self._client.post(
            f"/bonita/API/bpm/process/{process_id}/instantiation",
            headers=self._auth_headers,
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

    async def close(self) -> None:
        await self._client.aclose()
        self._csrf_token = None

    async def _get_task_by_case_id(self, case_id: str, max_retries: int = 10, retry_delay: float = 0.5) -> str:
        """Obtiene el taskId a partir del caseId con reintentos"""
        await self._ensure_session()

        for attempt in range(max_retries):
            params = {"f": f"caseId={case_id}"}
            response = await self._client.get("/bonita/API/bpm/userTask", params=params, headers=self._auth_headers)
            
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

    async def _get_logged_user(self) -> str:
        """Obtiene el ID del usuario logueado en Bonita"""
        await self._ensure_session()

        response = await self._client.get("/bonita/API/system/session/1", headers=self._auth_headers)
        
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
        await self._ensure_session()

        payload = {"assigned_id": user_id}
        response = await self._client.put(
            f"/bonita/API/bpm/userTask/{task_id}",
            headers=self._auth_headers,
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
        await self._ensure_session()

        response = await self._client.post(
            f"/bonita/API/bpm/userTask/{task_id}/execution",
            headers=self._auth_headers,
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


async def instantiate_project(project: ProjectCreate, initiator_username: str) -> Dict[str, Any]:
    client = BonitaClient()
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
    finally:
        await client.close()
