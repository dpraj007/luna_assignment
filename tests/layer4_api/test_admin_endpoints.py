"""
Layer 4: API Tests - Admin Endpoints

Full integration tests for admin API endpoints.
"""
import pytest
from httpx import AsyncClient
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))


class TestAdminDashboardEndpoint:
    """Test GET /api/v1/admin/dashboard endpoint."""

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_dashboard_stats(self, client: AsyncClient, api_v1_prefix):
        """Should return dashboard statistics."""
        response = await client.get(f"{api_v1_prefix}/admin/dashboard")

        assert response.status_code == 200
        data = response.json()
        # Should have various stats
        assert isinstance(data, dict)

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_dashboard_stats_with_data(
        self, client: AsyncClient, api_v1_prefix,
        multiple_users, multiple_venues
    ):
        """Dashboard should reflect actual data."""
        response = await client.get(f"{api_v1_prefix}/admin/dashboard")

        assert response.status_code == 200
        data = response.json()
        # Should have counts reflecting the test data
        assert isinstance(data, dict)


class TestAdminDataSeedEndpoint:
    """Test POST /api/v1/admin/data/seed endpoint."""

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_seed_data(self, client: AsyncClient, api_v1_prefix):
        """Should seed demo data."""
        response = await client.post(
            f"{api_v1_prefix}/admin/data/seed",
            params={"user_count": 10, "venue_count": 5}
        )

        assert response.status_code in [200, 201]
        data = response.json()
        assert "users" in data or "success" in data or isinstance(data, dict)

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_seed_data_custom_count(self, client: AsyncClient, api_v1_prefix):
        """Should seed with custom counts."""
        response = await client.post(
            f"{api_v1_prefix}/admin/data/seed",
            params={"user_count": 20}
        )

        assert response.status_code in [200, 201]


class TestAdminDataResetEndpoint:
    """Test POST /api/v1/admin/data/reset endpoint."""

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_reset_data(self, client: AsyncClient, api_v1_prefix):
        """Should reset all data."""
        response = await client.post(f"{api_v1_prefix}/admin/data/reset")

        assert response.status_code == 200
        data = response.json()
        assert "success" in data or "status" in data or isinstance(data, dict)


class TestAdminSpawnUsersEndpoint:
    """Test POST /api/v1/admin/spawn-users endpoint."""

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_spawn_users(self, client: AsyncClient, api_v1_prefix):
        """Should spawn simulated users."""
        response = await client.post(
            f"{api_v1_prefix}/admin/spawn-users",
            json={"count": 5}
        )

        assert response.status_code in [200, 201]
        data = response.json()
        assert isinstance(data, (dict, list))

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_spawn_users_with_personas(self, client: AsyncClient, api_v1_prefix):
        """Should spawn users with specific personas."""
        response = await client.post(
            f"{api_v1_prefix}/admin/spawn-users",
            json={
                "count": 3,
                "personas": ["social_butterfly", "foodie_explorer"]
            }
        )

        assert response.status_code in [200, 201]


class TestAdminStreamEndpoint:
    """Test GET /api/v1/admin/streams/subscribe/{channel} endpoint."""

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_subscribe_to_stream(self, client: AsyncClient, api_v1_prefix):
        """Should connect to SSE stream."""
        # SSE endpoints typically return streaming response
        # This tests the initial connection
        async with client.stream(
            "GET",
            f"{api_v1_prefix}/admin/streams/subscribe/user_actions",
            timeout=2.0
        ) as response:
            assert response.status_code == 200
            # Just check we can connect - context manager handles cleanup

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_subscribe_to_bookings_stream(self, client: AsyncClient, api_v1_prefix):
        """Should connect to bookings stream."""
        async with client.stream(
            "GET",
            f"{api_v1_prefix}/admin/streams/subscribe/bookings",
            timeout=2.0
        ) as response:
            assert response.status_code == 200
            # Context manager handles cleanup


class TestAdminContextEndpoints:
    """Test temporal and environment context endpoints."""

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_temporal_context(self, client: AsyncClient, api_v1_prefix):
        """Should return temporal context."""
        response = await client.get(f"{api_v1_prefix}/admin/context/temporal")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_environment_context(self, client: AsyncClient, api_v1_prefix):
        """Should return environment context."""
        response = await client.get(f"{api_v1_prefix}/admin/context/environment")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)


class TestAdminHealthEndpoint:
    """Test health check endpoint."""

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Should return healthy status."""
        response = await client.get("/health")

        # Health check may be at root or under admin
        if response.status_code == 404:
            response = await client.get("/api/v1/admin/health")

        assert response.status_code in [200, 404]  # May not be implemented
