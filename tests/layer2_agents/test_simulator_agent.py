"""
Layer 2: Agent Tests - Simulator Agent and Orchestrator

Tests user behavior simulation and orchestration logic.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from backend.app.agents.simulator_agent import (
    SimulatorAgent,
    SimulationOrchestrator,
    SimulationConfig,
    SimulationScenario,
    SimulationState,
)
from backend.app.models.user import User, UserPersona


class TestSimulationConfig:
    """Test simulation configuration."""

    @pytest.mark.layer2
    @pytest.mark.unit
    def test_default_config_values(self):
        """Default config should have expected values."""
        config = SimulationConfig()

        assert config.speed_multiplier == 1.0
        assert config.active_user_percentage == 0.3
        assert config.scenario == SimulationScenario.NORMAL
        assert sum(config.action_probability.values()) == pytest.approx(1.0, rel=0.01)

    @pytest.mark.layer2
    @pytest.mark.unit
    def test_action_probabilities_sum_to_one(self):
        """Action probabilities should sum to 1.0."""
        config = SimulationConfig()

        total = sum(config.action_probability.values())
        assert total == pytest.approx(1.0, rel=0.01)

    @pytest.mark.layer2
    @pytest.mark.unit
    def test_all_actions_defined(self):
        """All expected actions should be defined."""
        config = SimulationConfig()

        expected_actions = [
            "browse", "check_friends", "express_interest",
            "send_invite", "respond_invite", "make_booking"
        ]

        for action in expected_actions:
            assert action in config.action_probability


class TestSimulatorAgentActionWeights:
    """Test persona-based action weight adjustments."""

    @pytest.mark.layer2
    @pytest.mark.unit
    def test_social_butterfly_weights(self, db_session):
        """Social butterfly should have higher friend/invite weights."""
        user = User(
            id=1,
            email="social@test.com",
            username="social",
            persona=UserPersona.SOCIAL_BUTTERFLY
        )
        agent = SimulatorAgent(db_session, user)
        config = SimulationConfig()

        weights = agent._get_action_weights(config)

        # Social butterfly has 1.5x check_friends and send_invite
        assert weights["check_friends"] > config.action_probability["check_friends"]
        assert weights["send_invite"] > config.action_probability["send_invite"]

    @pytest.mark.layer2
    @pytest.mark.unit
    def test_foodie_explorer_weights(self, db_session):
        """Foodie explorer should have higher browse/interest weights."""
        user = User(
            id=1,
            email="foodie@test.com",
            username="foodie",
            persona=UserPersona.FOODIE_EXPLORER
        )
        agent = SimulatorAgent(db_session, user)
        config = SimulationConfig()

        weights = agent._get_action_weights(config)

        # Foodie has 1.3x browse and express_interest
        assert weights["browse"] > config.action_probability["browse"]
        assert weights["express_interest"] > config.action_probability["express_interest"]

    @pytest.mark.layer2
    @pytest.mark.unit
    def test_event_organizer_weights(self, db_session):
        """Event organizer should have higher invite/booking weights."""
        user = User(
            id=1,
            email="organizer@test.com",
            username="organizer",
            persona=UserPersona.EVENT_ORGANIZER
        )
        agent = SimulatorAgent(db_session, user)
        config = SimulationConfig()

        weights = agent._get_action_weights(config)

        # Event organizer has 2.0x send_invite, 1.5x booking
        assert weights["send_invite"] == config.action_probability["send_invite"] * 2.0
        assert weights["make_booking"] == config.action_probability["make_booking"] * 1.5

    @pytest.mark.layer2
    @pytest.mark.unit
    def test_busy_professional_weights(self, db_session):
        """Busy professional should have lower browse, higher booking."""
        user = User(
            id=1,
            email="busy@test.com",
            username="busy",
            persona=UserPersona.BUSY_PROFESSIONAL
        )
        agent = SimulatorAgent(db_session, user)
        config = SimulationConfig()

        weights = agent._get_action_weights(config)

        # Busy professional has 0.5x browse, 1.2x booking
        assert weights["browse"] < config.action_probability["browse"]
        assert weights["make_booking"] > config.action_probability["make_booking"]

    @pytest.mark.layer2
    @pytest.mark.unit
    def test_scenario_affects_weights(self, db_session):
        """Scenario should affect action weights."""
        user = User(
            id=1,
            email="test@test.com",
            username="test",
            persona=UserPersona.SOCIAL_BUTTERFLY
        )
        agent = SimulatorAgent(db_session, user)

        normal_config = SimulationConfig(scenario=SimulationScenario.NORMAL)
        lunch_config = SimulationConfig(scenario=SimulationScenario.LUNCH_RUSH)

        normal_weights = agent._get_action_weights(normal_config)
        lunch_weights = agent._get_action_weights(lunch_config)

        # Lunch rush should boost booking probability
        assert lunch_weights["make_booking"] > normal_weights["make_booking"]


class TestSimulatorAgentActionChoice:
    """Test action selection logic."""

    @pytest.mark.layer2
    @pytest.mark.unit
    def test_choose_action_returns_valid_action(self, db_session):
        """Chosen action should be from valid action list."""
        user = User(
            id=1,
            email="test@test.com",
            username="test",
            persona=UserPersona.SOCIAL_BUTTERFLY
        )
        agent = SimulatorAgent(db_session, user)
        config = SimulationConfig()

        valid_actions = [
            "browse", "check_friends", "express_interest",
            "send_invite", "respond_invite", "make_booking"
        ]

        for _ in range(100):
            action = agent._choose_action(config)
            assert action in valid_actions

    @pytest.mark.layer2
    @pytest.mark.unit
    def test_action_distribution_follows_weights(self, db_session):
        """Action distribution should roughly follow weights."""
        user = User(
            id=1,
            email="test@test.com",
            username="test",
            persona=None  # No persona for baseline
        )
        agent = SimulatorAgent(db_session, user)
        config = SimulationConfig()

        actions = {"browse": 0, "check_friends": 0, "express_interest": 0,
                   "send_invite": 0, "respond_invite": 0, "make_booking": 0}

        iterations = 10000
        for _ in range(iterations):
            action = agent._choose_action(config)
            actions[action] += 1

        # Check that browse (highest weight at 0.4) is most common
        browse_ratio = actions["browse"] / iterations
        assert 0.35 < browse_ratio < 0.45, f"Browse ratio {browse_ratio} outside expected range"


class TestSimulatorAgentActions:
    """Test individual simulated actions."""

    @pytest.mark.layer2
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_browse_venues_action(
        self, db_session, sample_user, multiple_venues
    ):
        """Browse venues action should return event data."""
        agent = SimulatorAgent(db_session, sample_user)
        simulation_time = datetime.utcnow()

        with patch.object(agent.streaming, 'publish_event', new_callable=AsyncMock):
            result = await agent._browse_venues(simulation_time)

            assert result["action"] == "browse"
            assert result["user_id"] == sample_user.id

    @pytest.mark.layer2
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_check_friends_action(
        self, db_session, users_with_friendships
    ):
        """Check friends action should return friend data."""
        users, friendships = users_with_friendships
        user = users[0]  # Alice has friends

        agent = SimulatorAgent(db_session, user)
        simulation_time = datetime.utcnow()

        with patch.object(agent.streaming, 'publish_event', new_callable=AsyncMock):
            result = await agent._check_friend_activity(simulation_time)

            assert result["action"] == "check_friends"
            assert result["user_id"] == user.id
            # Should have a friend_id since Alice has friends
            assert "friend_id" in result or result.get("result") == "no_friends"

    @pytest.mark.layer2
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_respond_invite_action(self, db_session, sample_user):
        """Respond to invite action should have acceptance rate."""
        agent = SimulatorAgent(db_session, sample_user)
        simulation_time = datetime.utcnow()

        acceptances = 0
        iterations = 100

        with patch.object(agent.streaming, 'publish_event', new_callable=AsyncMock):
            for _ in range(iterations):
                result = await agent._respond_to_invite(simulation_time)
                if result.get("accepted"):
                    acceptances += 1

        # Should have ~70% acceptance rate
        acceptance_rate = acceptances / iterations
        assert 0.5 < acceptance_rate < 0.9, f"Acceptance rate {acceptance_rate} outside expected range"


class TestSimulationOrchestrator:
    """Test the simulation orchestrator."""

    @pytest.mark.layer2
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_initial_state(self, db_session):
        """Initial state should be not running."""
        orchestrator = SimulationOrchestrator(db_session)

        assert orchestrator.state["running"] is False
        assert orchestrator.state["paused"] is False
        assert orchestrator.state["events_generated"] == 0

    @pytest.mark.layer2
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_start_simulation(self, db_session, multiple_users):
        """Starting simulation should update state."""
        # Make users simulated
        for user in multiple_users:
            user.is_simulated = True
        await db_session.commit()

        orchestrator = SimulationOrchestrator(db_session)

        with patch.object(orchestrator.streaming, 'publish_event', new_callable=AsyncMock):
            result = await orchestrator.start(speed=2.0, scenario="normal")

            assert result["status"] == "started"
            assert result["speed"] == 2.0
            assert orchestrator.state["running"] is True

            # Clean up
            await orchestrator.stop()

    @pytest.mark.layer2
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_pause_resume(self, db_session):
        """Pausing and resuming should update state."""
        orchestrator = SimulationOrchestrator(db_session)
        orchestrator.state["running"] = True

        with patch.object(orchestrator.streaming, 'publish_event', new_callable=AsyncMock):
            result = await orchestrator.pause()
            assert result["status"] == "paused"
            assert orchestrator.state["paused"] is True

            result = await orchestrator.resume()
            assert result["status"] == "resumed"
            assert orchestrator.state["paused"] is False

    @pytest.mark.layer2
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_stop_simulation(self, db_session):
        """Stopping simulation should return metrics."""
        orchestrator = SimulationOrchestrator(db_session)
        orchestrator.state["running"] = True
        orchestrator.state["events_generated"] = 100
        orchestrator.state["bookings_created"] = 5

        result = await orchestrator.stop()

        assert result["status"] == "stopped"
        assert result["events_generated"] == 100
        assert result["bookings_created"] == 5
        assert orchestrator.state["running"] is False

    @pytest.mark.layer2
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_set_speed(self, db_session):
        """Setting speed should update multiplier."""
        orchestrator = SimulationOrchestrator(db_session)

        result = await orchestrator.set_speed(10.0)

        assert result["speed"] == 10.0
        assert orchestrator.state["speed_multiplier"] == 10.0
        assert orchestrator.config.speed_multiplier == 10.0

    @pytest.mark.layer2
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_trigger_scenario(self, db_session):
        """Triggering scenario should update config."""
        orchestrator = SimulationOrchestrator(db_session)

        with patch.object(orchestrator.streaming, 'publish_event', new_callable=AsyncMock):
            result = await orchestrator.trigger_scenario("lunch_rush")

            assert result["scenario"] == "lunch_rush"
            assert orchestrator.state["scenario"] == "lunch_rush"
            # Lunch rush should have higher booking probability
            assert orchestrator.config.action_probability["make_booking"] == 0.15

    @pytest.mark.layer2
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_friday_night_scenario(self, db_session):
        """Friday night scenario should boost social actions."""
        orchestrator = SimulationOrchestrator(db_session)

        with patch.object(orchestrator.streaming, 'publish_event', new_callable=AsyncMock):
            await orchestrator.trigger_scenario("friday_night")

            # Friday night should have higher send_invite and check_friends
            assert orchestrator.config.action_probability["send_invite"] == 0.15
            assert orchestrator.config.action_probability["check_friends"] == 0.25

    @pytest.mark.layer2
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_state(self, db_session):
        """Get state should return current simulation state."""
        orchestrator = SimulationOrchestrator(db_session)
        orchestrator.state["events_generated"] = 50
        orchestrator.state["running"] = True

        state = await orchestrator.get_state()

        assert state["running"] is True
        assert state["events_generated"] == 50
        assert "simulation_time" in state

    @pytest.mark.layer2
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_metrics(self, db_session):
        """Get metrics should return simulation metrics."""
        orchestrator = SimulationOrchestrator(db_session)
        orchestrator.state["events_generated"] = 100
        orchestrator.state["bookings_created"] = 10
        orchestrator.state["invites_sent"] = 25

        metrics = await orchestrator.get_metrics()

        assert metrics["events_generated"] == 100
        assert metrics["bookings_created"] == 10
        assert metrics["invites_sent"] == 25
        assert "simulation_time" in metrics

    @pytest.mark.layer2
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_reset_simulation(self, db_session):
        """Reset should clear all state."""
        orchestrator = SimulationOrchestrator(db_session)
        orchestrator.state["events_generated"] = 100
        orchestrator.state["bookings_created"] = 10
        orchestrator.state["running"] = True

        with patch.object(orchestrator.streaming, 'publish_event', new_callable=AsyncMock):
            with patch.object(orchestrator.streaming, 'clear_streams', new_callable=AsyncMock):
                result = await orchestrator.reset()

                assert result["status"] == "reset"
                assert orchestrator.state["events_generated"] == 0
                assert orchestrator.state["bookings_created"] == 0
                assert orchestrator.state["running"] is False

    @pytest.mark.layer2
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_already_running_returns_status(self, db_session):
        """Starting already running simulation should return status."""
        orchestrator = SimulationOrchestrator(db_session)
        orchestrator.state["running"] = True

        result = await orchestrator.start()

        assert result["status"] == "already_running"


class TestScenarioDefinitions:
    """Test scenario enum and definitions."""

    @pytest.mark.layer2
    @pytest.mark.unit
    def test_all_scenarios_defined(self):
        """All expected scenarios should be defined."""
        expected = [
            "normal", "lunch_rush", "friday_night",
            "weekend_brunch", "concert_night", "new_user_onboarding"
        ]

        for scenario in expected:
            assert hasattr(SimulationScenario, scenario.upper())

    @pytest.mark.layer2
    @pytest.mark.unit
    def test_scenario_values_are_lowercase(self):
        """Scenario values should be lowercase strings."""
        for scenario in SimulationScenario:
            assert scenario.value.islower()
            assert "_" not in scenario.value or scenario.value == scenario.value.lower()
