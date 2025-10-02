from __future__ import annotations

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


async def instantiate_project(project: ProjectCreate, initiator_username: str) -> Dict[str, Any]:
    client = BonitaClient()
    try:
        response = await client.instantiate_process(project, initiator_username)
        logger.info("Bonita case created", response=response)
        return response
    finally:
        await client.close()
