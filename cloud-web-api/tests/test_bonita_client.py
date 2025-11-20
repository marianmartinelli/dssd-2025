import pytest
from unittest.mock import AsyncMock, patch
from app.services.bonita_client import BonitaClient, instantiate_project
from app.schemas.project import ProjectCreate, WorkPlanStage


@pytest.fixture
def sample_project():
    """Sample project data for testing."""
    return ProjectCreate(
        project_name="Test Project",
        project_description="A comprehensive test project for validating Bonita integration functionality.",
        project_category="Infrastructure",
        requesting_organization="Test ONG",
        contact_email="test@example.org",
        contact_phone="+54 11 1234-5678",
        estimated_budget=50000.0,
        currency="USD",
        start_date="2025-01-01",
        end_date="2025-12-31",
        priority_level="medium",
        supporting_docs_url="https://example.com/docs",
        work_plan_stages=[
            WorkPlanStage(
                stage_name="Initial Assessment",
                stage_start="2025-01-01",
                stage_end="2025-01-15",
                support_type="labor",
                description="Conduct initial site assessment and planning",
                estimated_amount=5000.0,
                amount_currency="USD"
            ),
            WorkPlanStage(
                stage_name="Implementation",
                stage_start="2025-02-01",
                stage_end="2025-11-30",
                support_type="materials",
                description="Execute main project activities",
                estimated_amount=40000.0,
                amount_currency="USD"
            )
        ]
    )


class TestBonitaClient:
    """Test cases for BonitaClient."""

    @pytest.mark.asyncio
    async def test_build_contract_payload(self, sample_project):
        """Test contract payload building."""
        client = BonitaClient()
        payload = client._build_contract_payload(sample_project, "test@example.org")
        
        assert "project" in payload
        project_data = payload["project"]
        
        assert project_data["projectName"] == "Test Project"
        assert project_data["currency"] == "USD"
        assert project_data["initiatorUserId"] == "test@example.org"
        assert len(project_data["workPlanStages"]) == 2
        assert project_data["workPlanStages"][0]["stageName"] == "Initial Assessment"

    @pytest.mark.asyncio
    async def test_map_stage(self, sample_project):
        """Test work plan stage mapping."""
        client = BonitaClient()
        stage = sample_project.work_plan_stages[0]
        mapped_stage = client._map_stage(stage)
        
        assert mapped_stage["stageName"] == "Initial Assessment"
        assert mapped_stage["supportType"] == "labor"
        assert mapped_stage["estimatedAmount"] == 5000.0
        assert mapped_stage["amountCurrency"] == "USD"

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_session_establishment_success(self, mock_client_class, sample_project):
        """Test successful Bonita session establishment."""
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        
        # Mock successful login response
        mock_response = AsyncMock()
        mock_response.status_code = 204
        mock_response.headers = {"set-cookie": "JSESSIONID=test-session"}
        mock_client.post.return_value = mock_response
        
        client = BonitaClient()
        await client._ensure_session()
        
        assert client._session_cookie == "JSESSIONID=test-session"
        mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_session_establishment_failure(self, mock_client_class):
        """Test failed Bonita session establishment."""
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        
        # Mock failed login response
        mock_response = AsyncMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_client.post.return_value = mock_response
        
        client = BonitaClient()
        
        with pytest.raises(Exception):  # Should raise HTTPException
            await client._ensure_session()

    @pytest.mark.asyncio
    @patch('app.services.bonita_client.BonitaClient')
    async def test_instantiate_project_function(self, mock_client_class, sample_project):
        """Test the instantiate_project function."""
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        
        mock_response = {
            "caseId": 12345,
            "processDefinitionId": "process-def-123"
        }
        mock_client.instantiate_process.return_value = mock_response
        
        result = await instantiate_project(sample_project, "test@example.org")
        
        assert result == mock_response
        mock_client.instantiate_process.assert_called_once_with(sample_project, "test@example.org")
        mock_client.close.assert_called_once()
