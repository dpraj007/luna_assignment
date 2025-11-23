"""
Layer 4: API Tests - Simulation Endpoints

Full integration tests for simulation control API endpoints.
"""
import pytest
from httpx import AsyncClient
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))


class TestSimulationStartEndpoint:
    """Test POST /api/v1/simulation/start endpoint."""

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_start_simulation(self, client: AsyncClient, api_v1_prefix):
        """Should start simulation."""
        response = await client.post(
            f"{api_v1_prefix}/simulation/start",
            json={"speed": 1.0, "scenario": "normal"}
        )

        assert response.status_code in [200, 201]
        data = response.json()
        assert data.get("status") in ["started", "already_running"]

        # Clean up - stop simulation
        await client.post(f"{api_v1_prefix}/simulation/stop")

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_start_simulation_with_speed(self, client: AsyncClient, api_v1_prefix):
        """Should start simulation with custom speed."""
        response = await client.post(
            f"{api_v1_prefix}/simulation/start",
            json={"speed": 10.0, "scenario": "normal"}
        )

        assert response.status_code in [200, 201]
        data = response.json()
        if data.get("status") == "started":
            assert data.get("speed") == 10.0

        # Clean up
        await client.post(f"{api_v1_prefix}/simulation/stop")

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_start_simulation_with_scenario(self, client: AsyncClient, api_v1_prefix):
        """Should start simulation with specific scenario."""
        response = await client.post(
            f"{api_v1_prefix}/simulation/start",
            json={"speed": 1.0, "scenario": "lunch_rush"}
        )

        assert response.status_code in [200, 201]
        data = response.json()
        if data.get("status") == "started":
            assert data.get("scenario") == "lunch_rush"

        # Clean up
        await client.post(f"{api_v1_prefix}/simulation/stop")


class TestSimulationPauseResumeEndpoint:
    """Test POST /api/v1/simulation/pause and /resume endpoints."""

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_pause_simulation(self, client: AsyncClient, api_v1_prefix):
        """Should pause running simulation."""
        # Start simulation first
        await client.post(
            f"{api_v1_prefix}/simulation/start",
            json={"speed": 1.0, "scenario": "normal"}
        )

        response = await client.post(f"{api_v1_prefix}/simulation/pause")

        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "paused"

        # Clean up
        await client.post(f"{api_v1_prefix}/simulation/stop")

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_resume_simulation(self, client: AsyncClient, api_v1_prefix):
        """Should resume paused simulation."""
        # Start and pause
        await client.post(
            f"{api_v1_prefix}/simulation/start",
            json={"speed": 1.0, "scenario": "normal"}
        )
        await client.post(f"{api_v1_prefix}/simulation/pause")

        response = await client.post(f"{api_v1_prefix}/simulation/resume")

        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "resumed"

        # Clean up
        await client.post(f"{api_v1_prefix}/simulation/stop")


class TestSimulationStopEndpoint:
    """Test POST /api/v1/simulation/stop endpoint."""

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_stop_simulation(self, client: AsyncClient, api_v1_prefix):
        """Should stop simulation and return metrics."""
        # Start simulation first
        await client.post(
            f"{api_v1_prefix}/simulation/start",
            json={"speed": 1.0, "scenario": "normal"}
        )

        response = await client.post(f"{api_v1_prefix}/simulation/stop")

        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "stopped"


class TestSimulationStateEndpoint:
    """Test GET /api/v1/simulation/state endpoint."""

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_simulation_state(self, client: AsyncClient, api_v1_prefix):
        """Should return current simulation state."""
        response = await client.get(f"{api_v1_prefix}/simulation/state")

        assert response.status_code == 200
        data = response.json()
        assert "running" in data
        assert "paused" in data


class TestSimulationMetricsEndpoint:
    """Test GET /api/v1/simulation/metrics endpoint."""

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_simulation_metrics(self, client: AsyncClient, api_v1_prefix):
        """Should return simulation metrics."""
        response = await client.get(f"{api_v1_prefix}/simulation/metrics")

        assert response.status_code == 200
        data = response.json()
        assert "events_generated" in data
        assert "bookings_created" in data


class TestSimulationSpeedEndpoint:
    """Test POST /api/v1/simulation/speed endpoint."""

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_set_simulation_speed(self, client: AsyncClient, api_v1_prefix):
        """Should update simulation speed."""
        response = await client.post(
            f"{api_v1_prefix}/simulation/speed",
            json={"speed": 50.0}
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get("speed") == 50.0


class TestSimulationScenarioEndpoint:
    """Test POST /api/v1/simulation/scenario endpoint."""

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_trigger_scenario(self, client: AsyncClient, api_v1_prefix):
        """Should trigger specific scenario."""
        response = await client.post(
            f"{api_v1_prefix}/simulation/scenario",
            json={"scenario": "friday_night"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get("scenario") == "friday_night"

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_trigger_lunch_rush_scenario(self, client: AsyncClient, api_v1_prefix):
        """Should trigger lunch rush scenario."""
        response = await client.post(
            f"{api_v1_prefix}/simulation/scenario",
            json={"scenario": "lunch_rush"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get("scenario") == "lunch_rush"
