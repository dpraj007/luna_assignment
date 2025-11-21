"""
Simulator Agent - Creates realistic user behavior for demo.

This agent simulates a living ecosystem of users interacting with
the platform, demonstrating the AI capabilities in action.
"""
from typing import TypedDict, List, Optional, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import asyncio
import random
import logging
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ..models.user import User, UserPersona, Friendship
from ..models.venue import Venue
from ..models.interaction import VenueInterest
from ..models.event import EventType
from ..services.streaming import get_streaming_service
from .booking_agent import BookingAgent
from .recommendation_agent import RecommendationAgent

logger = logging.getLogger(__name__)


class SimulationScenario(str, Enum):
    """Pre-programmed simulation scenarios."""
    NORMAL = "normal"
    LUNCH_RUSH = "lunch_rush"
    FRIDAY_NIGHT = "friday_night"
    WEEKEND_BRUNCH = "weekend_brunch"
    CONCERT_NIGHT = "concert_night"
    NEW_USER_ONBOARDING = "new_user_onboarding"


@dataclass
class SimulationConfig:
    """Configuration for simulation behavior."""
    speed_multiplier: float = 1.0
    active_user_percentage: float = 0.3
    action_probability: Dict[str, float] = None
    scenario: SimulationScenario = SimulationScenario.NORMAL

    def __post_init__(self):
        if self.action_probability is None:
            self.action_probability = {
                "browse": 0.40,
                "check_friends": 0.20,
                "express_interest": 0.15,
                "send_invite": 0.10,
                "respond_invite": 0.10,
                "make_booking": 0.05,
            }


class SimulationState(TypedDict):
    """Global simulation state."""
    running: bool
    paused: bool
    simulation_time: datetime
    speed_multiplier: float
    scenario: str
    active_users: List[int]
    events_generated: int
    bookings_created: int
    invites_sent: int


class SimulatorAgent:
    """
    Agent that simulates individual user behavior.

    Each simulated user has:
    - A persona that influences behavior
    - Preferences that guide choices
    - Social connections that affect interactions
    """

    def __init__(self, db: AsyncSession, user: User):
        self.db = db
        self.user = user
        self.streaming = get_streaming_service()
        self.recommendation_agent = RecommendationAgent(db)
        self.booking_agent = BookingAgent(db)

    def _get_action_weights(self, config: SimulationConfig) -> Dict[str, float]:
        """Get action weights based on persona and scenario."""
        weights = config.action_probability.copy()

        # Adjust based on persona
        if self.user.persona == UserPersona.SOCIAL_BUTTERFLY:
            weights["check_friends"] *= 1.5
            weights["send_invite"] *= 1.5
        elif self.user.persona == UserPersona.FOODIE_EXPLORER:
            weights["browse"] *= 1.3
            weights["express_interest"] *= 1.3
        elif self.user.persona == UserPersona.EVENT_ORGANIZER:
            weights["send_invite"] *= 2.0
            weights["make_booking"] *= 1.5
        elif self.user.persona == UserPersona.SPONTANEOUS_DINER:
            weights["make_booking"] *= 1.5
        elif self.user.persona == UserPersona.ROUTINE_REGULAR:
            weights["browse"] *= 0.7  # Less browsing, more consistent
        elif self.user.persona == UserPersona.BUSY_PROFESSIONAL:
            weights["browse"] *= 0.5
            weights["make_booking"] *= 1.2

        # Adjust for scenario
        if config.scenario == SimulationScenario.LUNCH_RUSH:
            weights["make_booking"] *= 2.0
            weights["browse"] *= 1.5
        elif config.scenario == SimulationScenario.FRIDAY_NIGHT:
            weights["send_invite"] *= 2.0
            weights["check_friends"] *= 1.5
        elif config.scenario == SimulationScenario.WEEKEND_BRUNCH:
            weights["express_interest"] *= 1.5

        return weights

    def _choose_action(self, config: SimulationConfig) -> str:
        """Choose an action based on weighted probabilities."""
        weights = self._get_action_weights(config)
        actions = list(weights.keys())
        probabilities = list(weights.values())

        # Normalize probabilities
        total = sum(probabilities)
        probabilities = [p / total for p in probabilities]

        return random.choices(actions, weights=probabilities)[0]

    async def perform_action(
        self,
        config: SimulationConfig,
        simulation_time: datetime
    ) -> Optional[dict]:
        """
        Perform a simulated action for this user.

        Returns event data if action was performed.
        """
        action = self._choose_action(config)
        event_data = None

        try:
            if action == "browse":
                event_data = await self._browse_venues(simulation_time)
            elif action == "check_friends":
                event_data = await self._check_friend_activity(simulation_time)
            elif action == "express_interest":
                event_data = await self._express_interest(simulation_time)
            elif action == "send_invite":
                event_data = await self._send_invite(simulation_time)
            elif action == "respond_invite":
                event_data = await self._respond_to_invite(simulation_time)
            elif action == "make_booking":
                event_data = await self._make_booking(simulation_time)
        except Exception as e:
            logger.error(f"Error performing action {action} for user {self.user.id}: {e}")

        return event_data

    async def _browse_venues(self, simulation_time: datetime) -> dict:
        """Simulate browsing venues."""
        # Get recommendations
        recs = await self.recommendation_agent.get_recommendations(self.user.id)

        if recs["venues"]:
            viewed_venue = random.choice(recs["venues"])
            duration = random.randint(5, 60)  # Viewing duration in seconds

            await self.streaming.publish_event(
                event_type="user_browse",
                channel="user_actions",
                payload={
                    "action": "browse_venue",
                    "venue_id": viewed_venue["id"],
                    "venue_name": viewed_venue["name"],
                    "duration_seconds": duration,
                },
                simulation_time=simulation_time,
                user_id=self.user.id,
                venue_id=viewed_venue["id"]
            )

            return {
                "action": "browse",
                "user_id": self.user.id,
                "venue_id": viewed_venue["id"],
                "venue_name": viewed_venue["name"]
            }

        return {"action": "browse", "user_id": self.user.id, "result": "no_venues"}

    async def _check_friend_activity(self, simulation_time: datetime) -> dict:
        """Simulate checking friend activity."""
        # Get friends
        query = select(Friendship).where(Friendship.user_id == self.user.id).limit(5)
        result = await self.db.execute(query)
        friends = result.scalars().all()

        if friends:
            friend = random.choice(friends)

            await self.streaming.publish_event(
                event_type="user_browse",
                channel="user_actions",
                payload={
                    "action": "check_friends",
                    "friend_id": friend.friend_id,
                },
                simulation_time=simulation_time,
                user_id=self.user.id
            )

            return {
                "action": "check_friends",
                "user_id": self.user.id,
                "friend_id": friend.friend_id
            }

        return {"action": "check_friends", "user_id": self.user.id, "result": "no_friends"}

    async def _express_interest(self, simulation_time: datetime) -> dict:
        """Simulate expressing interest in a venue."""
        # Get a random venue
        query = select(Venue).order_by(func.random()).limit(1)
        result = await self.db.execute(query)
        venue = result.scalar_one_or_none()

        if venue:
            time_slots = ["breakfast", "lunch", "dinner", "brunch"]
            preferred_slot = random.choice(time_slots)

            result = await self.recommendation_agent.express_interest(
                user_id=self.user.id,
                venue_id=venue.id,
                preferred_time_slot=preferred_slot,
                open_to_invites=random.random() > 0.3
            )

            return {
                "action": "express_interest",
                "user_id": self.user.id,
                "venue_id": venue.id,
                "venue_name": venue.name,
                "others_interested": len(result.get("others_interested", []))
            }

        return {"action": "express_interest", "user_id": self.user.id, "result": "no_venue"}

    async def _send_invite(self, simulation_time: datetime) -> dict:
        """Simulate sending an invitation."""
        # Get a random friend
        query = select(Friendship).where(Friendship.user_id == self.user.id).limit(1)
        result = await self.db.execute(query)
        friendship = result.scalar_one_or_none()

        if not friendship:
            return {"action": "send_invite", "user_id": self.user.id, "result": "no_friends"}

        # Get a venue both might like
        venue_query = select(Venue).order_by(func.random()).limit(1)
        venue_result = await self.db.execute(venue_query)
        venue = venue_result.scalar_one_or_none()

        if venue:
            await self.streaming.publish_event(
                event_type="invite_sent",
                channel="social",
                payload={
                    "inviter_id": self.user.id,
                    "invitee_id": friendship.friend_id,
                    "venue_id": venue.id,
                    "venue_name": venue.name,
                },
                simulation_time=simulation_time,
                user_id=self.user.id,
                venue_id=venue.id
            )

            return {
                "action": "send_invite",
                "user_id": self.user.id,
                "invitee_id": friendship.friend_id,
                "venue_id": venue.id,
                "venue_name": venue.name
            }

        return {"action": "send_invite", "user_id": self.user.id, "result": "no_venue"}

    async def _respond_to_invite(self, simulation_time: datetime) -> dict:
        """Simulate responding to an invitation."""
        # Simplified: just emit an event (would normally check pending invites)
        accepted = random.random() > 0.3  # 70% acceptance rate

        await self.streaming.publish_event(
            event_type="invite_response",
            channel="social",
            payload={
                "user_id": self.user.id,
                "accepted": accepted,
            },
            simulation_time=simulation_time,
            user_id=self.user.id
        )

        return {
            "action": "respond_invite",
            "user_id": self.user.id,
            "accepted": accepted
        }

    async def _make_booking(self, simulation_time: datetime) -> dict:
        """Simulate making a booking."""
        # Get user's interests
        query = select(VenueInterest).where(
            VenueInterest.user_id == self.user.id,
            VenueInterest.explicitly_interested == 1
        ).limit(1)
        result = await self.db.execute(query)
        interest = result.scalar_one_or_none()

        if not interest:
            # Get random venue
            venue_query = select(Venue).order_by(func.random()).limit(1)
            venue_result = await self.db.execute(venue_query)
            venue = venue_result.scalar_one_or_none()
            venue_id = venue.id if venue else None
        else:
            venue_id = interest.venue_id

        if venue_id:
            # Create booking through agent
            booking_result = await self.booking_agent.create_booking(
                user_id=self.user.id,
                venue_id=venue_id,
                party_size=random.randint(2, 4),
                preferred_time=simulation_time + timedelta(hours=random.randint(1, 48))
            )

            return {
                "action": "make_booking",
                "user_id": self.user.id,
                "venue_id": venue_id,
                "success": booking_result.get("success", False),
                "booking_id": booking_result.get("booking_id")
            }

        return {"action": "make_booking", "user_id": self.user.id, "result": "no_venue"}


class SimulationOrchestrator:
    """
    Master orchestrator for the simulation.

    Controls:
    - Simulation time
    - Active user pool
    - Event generation rate
    - Scenario triggers
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.streaming = get_streaming_service()

        self.state: SimulationState = {
            "running": False,
            "paused": False,
            "simulation_time": datetime.utcnow(),
            "speed_multiplier": 1.0,
            "scenario": SimulationScenario.NORMAL.value,
            "active_users": [],
            "events_generated": 0,
            "bookings_created": 0,
            "invites_sent": 0,
        }

        self.config = SimulationConfig()
        self._task: Optional[asyncio.Task] = None

    async def start(self, speed: float = 1.0, scenario: str = "normal"):
        """Start the simulation."""
        if self.state["running"]:
            return {"status": "already_running"}

        self.state["running"] = True
        self.state["paused"] = False
        self.state["speed_multiplier"] = speed
        self.state["scenario"] = scenario
        self.state["simulation_time"] = datetime.utcnow()

        self.config.speed_multiplier = speed
        self.config.scenario = SimulationScenario(scenario)

        # Load active users
        await self._load_active_users()

        # Publish start event
        await self.streaming.publish_event(
            event_type="simulation_started",
            channel="simulation",
            payload={
                "speed": speed,
                "scenario": scenario,
                "active_users": len(self.state["active_users"]),
            },
            simulation_time=self.state["simulation_time"]
        )

        # Start simulation loop
        self._task = asyncio.create_task(self._simulation_loop())

        return {
            "status": "started",
            "speed": speed,
            "scenario": scenario,
            "active_users": len(self.state["active_users"])
        }

    async def pause(self):
        """Pause the simulation."""
        self.state["paused"] = True

        await self.streaming.publish_event(
            event_type="simulation_paused",
            channel="simulation",
            payload={"simulation_time": self.state["simulation_time"].isoformat()},
            simulation_time=self.state["simulation_time"]
        )

        return {"status": "paused"}

    async def resume(self):
        """Resume the simulation."""
        self.state["paused"] = False

        await self.streaming.publish_event(
            event_type="simulation_resumed",
            channel="simulation",
            payload={"simulation_time": self.state["simulation_time"].isoformat()},
            simulation_time=self.state["simulation_time"]
        )

        return {"status": "resumed"}

    async def stop(self):
        """Stop the simulation."""
        self.state["running"] = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        return {
            "status": "stopped",
            "events_generated": self.state["events_generated"],
            "bookings_created": self.state["bookings_created"]
        }

    async def reset(self):
        """Reset simulation state."""
        await self.stop()

        self.state = {
            "running": False,
            "paused": False,
            "simulation_time": datetime.utcnow(),
            "speed_multiplier": 1.0,
            "scenario": SimulationScenario.NORMAL.value,
            "active_users": [],
            "events_generated": 0,
            "bookings_created": 0,
            "invites_sent": 0,
        }

        await self.streaming.clear_streams()

        await self.streaming.publish_event(
            event_type="simulation_reset",
            channel="simulation",
            payload={},
            simulation_time=datetime.utcnow()
        )

        return {"status": "reset"}

    async def set_speed(self, multiplier: float):
        """Set simulation speed multiplier."""
        self.state["speed_multiplier"] = multiplier
        self.config.speed_multiplier = multiplier
        return {"speed": multiplier}

    async def trigger_scenario(self, scenario: str):
        """Trigger a specific scenario."""
        self.state["scenario"] = scenario
        self.config.scenario = SimulationScenario(scenario)

        # Adjust probabilities for scenario
        if scenario == "lunch_rush":
            self.config.action_probability = {
                "browse": 0.50,
                "check_friends": 0.15,
                "express_interest": 0.15,
                "send_invite": 0.08,
                "respond_invite": 0.07,
                "make_booking": 0.15,
            }
        elif scenario == "friday_night":
            self.config.action_probability = {
                "browse": 0.30,
                "check_friends": 0.25,
                "express_interest": 0.15,
                "send_invite": 0.15,
                "respond_invite": 0.10,
                "make_booking": 0.05,
            }
        else:
            # Reset to normal
            self.config.action_probability = {
                "browse": 0.40,
                "check_friends": 0.20,
                "express_interest": 0.15,
                "send_invite": 0.10,
                "respond_invite": 0.10,
                "make_booking": 0.05,
            }

        await self.streaming.publish_event(
            event_type="scenario_triggered",
            channel="simulation",
            payload={"scenario": scenario},
            simulation_time=self.state["simulation_time"]
        )

        return {"scenario": scenario}

    async def get_state(self) -> dict:
        """Get current simulation state."""
        return {
            **self.state,
            "simulation_time": self.state["simulation_time"].isoformat()
        }

    async def get_metrics(self) -> dict:
        """Get simulation metrics."""
        return {
            "events_generated": self.state["events_generated"],
            "bookings_created": self.state["bookings_created"],
            "invites_sent": self.state["invites_sent"],
            "active_users": len(self.state["active_users"]),
            "simulation_time": self.state["simulation_time"].isoformat(),
            "speed_multiplier": self.state["speed_multiplier"],
            "scenario": self.state["scenario"],
            "running": self.state["running"],
            "paused": self.state["paused"],
        }

    async def _load_active_users(self):
        """Load pool of active simulated users."""
        query = select(User).where(User.is_simulated == True).limit(100)
        result = await self.db.execute(query)
        users = result.scalars().all()

        # Select percentage of users to be active
        num_active = int(len(users) * self.config.active_user_percentage)
        self.state["active_users"] = [u.id for u in random.sample(users, min(num_active, len(users)))]

    async def _simulation_loop(self):
        """Main simulation loop."""
        while self.state["running"]:
            if self.state["paused"]:
                await asyncio.sleep(0.5)
                continue

            # Advance simulation time
            time_delta = timedelta(seconds=1) * self.state["speed_multiplier"]
            self.state["simulation_time"] += time_delta

            # Process a batch of users
            batch_size = max(1, int(len(self.state["active_users"]) * 0.1))
            active_batch = random.sample(
                self.state["active_users"],
                min(batch_size, len(self.state["active_users"]))
            )

            for user_id in active_batch:
                # Get user
                query = select(User).where(User.id == user_id)
                result = await self.db.execute(query)
                user = result.scalar_one_or_none()

                if user:
                    agent = SimulatorAgent(self.db, user)
                    event = await agent.perform_action(
                        self.config,
                        self.state["simulation_time"]
                    )

                    if event:
                        self.state["events_generated"] += 1

                        if event.get("action") == "make_booking" and event.get("success"):
                            self.state["bookings_created"] += 1
                        elif event.get("action") == "send_invite":
                            self.state["invites_sent"] += 1

            # Emit metrics periodically
            if self.state["events_generated"] % 10 == 0:
                await self.streaming.publish_event(
                    event_type="metrics_update",
                    channel="metrics",
                    payload=await self.get_metrics(),
                    simulation_time=self.state["simulation_time"]
                )

            # Sleep based on speed (faster = shorter sleep)
            await asyncio.sleep(1.0 / self.state["speed_multiplier"])
