"""
LangGraph-based Simulator Agent.

This module implements the simulation system using LangGraph's state graph
architecture for better control flow and state management.
"""
from typing import TypedDict, List, Dict, Any, Optional, Annotated
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import asyncio
import random
import logging
import operator

from langgraph.graph import StateGraph, END
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ..models.user import User, UserPersona, Friendship, UserPreferences
from ..models.venue import Venue
from ..models.interaction import VenueInterest
from ..models.booking import Booking
from ..services.streaming import get_streaming_service
from .booking_agent import BookingAgent
from .recommendation_agent import RecommendationAgent

logger = logging.getLogger(__name__)


# ============================================================================
# State Definitions
# ============================================================================

class SimulationGraphState(TypedDict):
    """
    LangGraph state for simulation.

    This state is passed through all nodes in the graph.
    """
    # Simulation time management
    simulation_time: datetime
    speed_multiplier: float

    # User pool
    active_users: List[int]
    user_pool_size: int

    # Pending events and actions
    pending_events: List[dict]
    selected_actions: Dict[int, dict]  # user_id -> action details
    executed_events: List[dict]

    # Venue states
    venue_states: Dict[int, dict]  # venue_id -> {availability, trending, etc.}

    # Social graph
    social_graph: Dict[int, List[int]]  # user_id -> list of friend_ids

    # Metrics
    metrics: Dict[str, Any]

    # Configuration
    scenario: str
    action_probabilities: Dict[str, float]
    persona_modifiers: Dict[str, Dict[str, float]]
    temporal_modifiers: Dict[str, float]

    # Control flags
    is_running: bool
    is_paused: bool

    # Database session (passed through)
    db_session_id: str  # Reference to session


@dataclass
class SimulationConfig:
    """Configuration for simulation behavior."""
    speed_multiplier: float = 1.0
    active_user_percentage: float = 0.3
    tick_interval: float = 1.0
    max_actions_per_tick: int = 10

    base_action_probabilities: Dict[str, float] = field(default_factory=lambda: {
        "browse": 0.40,
        "check_friends": 0.20,
        "express_interest": 0.15,
        "send_invite": 0.10,
        "respond_invite": 0.10,
        "make_booking": 0.05,
    })

    persona_modifiers: Dict[str, Dict[str, float]] = field(default_factory=lambda: {
        "social_butterfly": {"check_friends": 1.5, "send_invite": 1.5},
        "foodie_explorer": {"browse": 1.3, "express_interest": 1.3},
        "event_organizer": {"send_invite": 2.0, "make_booking": 1.5},
        "spontaneous_diner": {"make_booking": 1.5},
        "routine_regular": {"browse": 0.7},
        "busy_professional": {"browse": 0.5, "make_booking": 1.2},
        "budget_conscious": {"browse": 1.2, "express_interest": 0.8},
    })

    scenario_modifiers: Dict[str, Dict[str, float]] = field(default_factory=lambda: {
        "normal": {},
        "lunch_rush": {"browse": 1.5, "make_booking": 2.0},
        "friday_night": {"send_invite": 2.0, "check_friends": 1.5},
        "weekend_brunch": {"express_interest": 1.5, "browse": 1.3},
        "concert_night": {"send_invite": 1.5, "make_booking": 1.5},
        "new_user_onboarding": {"browse": 2.0, "check_friends": 1.5},
    })


# ============================================================================
# Graph Nodes
# ============================================================================

async def user_pool_manager(state: SimulationGraphState, db: AsyncSession) -> dict:
    """
    Node 1: UserPoolManager

    Maintains the pool of active simulated users.
    - Loads users from database if pool is empty
    - Filters by is_simulated=True
    - Applies active_user_percentage from config
    - Updates social_graph for loaded users
    """
    logger.debug("UserPoolManager: Managing user pool")

    updates = {}

    # If we don't have active users, load them
    if not state.get("active_users"):
        query = select(User).where(User.is_simulated == True).limit(100)
        result = await db.execute(query)
        users = result.scalars().all()

        if users:
            # Select percentage to be active
            pool_size = state.get("user_pool_size", 30)
            active_percentage = min(1.0, pool_size / len(users)) if users else 0.3
            num_active = int(len(users) * active_percentage)
            active_users = [u.id for u in random.sample(users, min(num_active, len(users)))]
            updates["active_users"] = active_users

            # Build social graph
            social_graph = {}
            for user_id in active_users:
                query = select(Friendship.friend_id).where(Friendship.user_id == user_id)
                result = await db.execute(query)
                friends = result.scalars().all()
                social_graph[user_id] = list(friends)

            updates["social_graph"] = social_graph

            logger.info(f"UserPoolManager: Loaded {len(active_users)} active users")

    # Update metrics
    metrics = state.get("metrics", {})
    metrics["active_user_count"] = len(state.get("active_users", []) or updates.get("active_users", []))
    updates["metrics"] = metrics

    return updates


async def behavior_engine(state: SimulationGraphState, db: AsyncSession) -> dict:
    """
    Node 2: BehaviorEngine

    Decides next action for each active user based on:
    - Base action probabilities
    - Persona modifiers
    - Scenario modifiers
    - Temporal modifiers (from TemporalEventGenerator)
    """
    logger.debug("BehaviorEngine: Selecting actions for users")

    active_users = state.get("active_users", [])
    if not active_users:
        return {"selected_actions": {}}

    base_probs = state.get("action_probabilities", {
        "browse": 0.40,
        "check_friends": 0.20,
        "express_interest": 0.15,
        "send_invite": 0.10,
        "respond_invite": 0.10,
        "make_booking": 0.05,
    })

    scenario = state.get("scenario", "normal")
    temporal_mods = state.get("temporal_modifiers", {})
    persona_mods = state.get("persona_modifiers", {})

    # Scenario modifiers
    scenario_mods = {
        "normal": {},
        "lunch_rush": {"browse": 1.5, "make_booking": 2.0},
        "friday_night": {"send_invite": 2.0, "check_friends": 1.5},
        "weekend_brunch": {"express_interest": 1.5},
        "concert_night": {"send_invite": 1.5, "make_booking": 1.5},
    }.get(scenario, {})

    selected_actions = {}

    # Select a batch of users to act this tick
    batch_size = min(10, len(active_users))
    batch_users = random.sample(active_users, batch_size)

    for user_id in batch_users:
        # Get user persona
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            continue

        # Calculate weighted probabilities
        weights = base_probs.copy()

        # Apply persona modifiers
        persona_key = user.persona.value if user.persona else "routine_regular"
        user_persona_mods = persona_mods.get(persona_key, {})
        for action, mod in user_persona_mods.items():
            if action in weights:
                weights[action] *= mod

        # Apply scenario modifiers
        for action, mod in scenario_mods.items():
            if action in weights:
                weights[action] *= mod

        # Apply temporal modifiers
        for action, mod in temporal_mods.items():
            if action in weights:
                weights[action] *= mod

        # Normalize and select
        actions = list(weights.keys())
        probs = list(weights.values())
        total = sum(probs)
        probs = [p / total for p in probs]

        selected_action = random.choices(actions, weights=probs)[0]

        selected_actions[user_id] = {
            "action": selected_action,
            "user": user,
            "timestamp": state.get("simulation_time", datetime.utcnow()),
        }

    logger.debug(f"BehaviorEngine: Selected {len(selected_actions)} actions")
    return {"selected_actions": selected_actions}


async def action_executor(state: SimulationGraphState, db: AsyncSession) -> dict:
    """
    Node 3: ActionExecutor

    Performs the selected actions in the system.
    Executes each action and collects event data.
    """
    logger.debug("ActionExecutor: Executing actions")

    selected_actions = state.get("selected_actions", {})
    if not selected_actions:
        return {"executed_events": []}

    streaming = get_streaming_service()
    simulation_time = state.get("simulation_time", datetime.utcnow())
    executed_events = []

    for user_id, action_data in selected_actions.items():
        action = action_data["action"]
        user = action_data["user"]

        try:
            event = None

            if action == "browse":
                event = await _execute_browse(db, user, simulation_time, streaming)
            elif action == "check_friends":
                event = await _execute_check_friends(db, user, simulation_time, streaming, state)
            elif action == "express_interest":
                event = await _execute_express_interest(db, user, simulation_time, streaming)
            elif action == "send_invite":
                event = await _execute_send_invite(db, user, simulation_time, streaming, state)
            elif action == "respond_invite":
                event = await _execute_respond_invite(db, user, simulation_time, streaming)
            elif action == "make_booking":
                event = await _execute_make_booking(db, user, simulation_time, streaming)

            if event:
                event["user_id"] = user_id
                event["timestamp"] = simulation_time.isoformat()
                executed_events.append(event)

        except Exception as e:
            logger.error(f"ActionExecutor: Error executing {action} for user {user_id}: {e}")

    logger.debug(f"ActionExecutor: Executed {len(executed_events)} events")
    return {"executed_events": executed_events}


async def state_updater(state: SimulationGraphState, db: AsyncSession) -> dict:
    """
    Node 4: StateUpdater

    Updates user state and preferences based on executed actions.
    - Updates venue states (trending, availability)
    - Updates social graph
    - Updates metrics
    """
    logger.debug("StateUpdater: Updating state")

    executed_events = state.get("executed_events", [])
    metrics = state.get("metrics", {}).copy()
    venue_states = state.get("venue_states", {}).copy()
    social_graph = state.get("social_graph", {}).copy()

    # Process events and update metrics
    for event in executed_events:
        action = event.get("action")

        # Update metrics
        metrics["events_generated"] = metrics.get("events_generated", 0) + 1

        if action == "make_booking" and event.get("success"):
            metrics["bookings_created"] = metrics.get("bookings_created", 0) + 1
        elif action == "send_invite":
            metrics["invites_sent"] = metrics.get("invites_sent", 0) + 1
        elif action == "browse":
            metrics["browse_count"] = metrics.get("browse_count", 0) + 1

        # Update venue states
        venue_id = event.get("venue_id")
        if venue_id:
            if venue_id not in venue_states:
                venue_states[venue_id] = {"view_count": 0, "booking_count": 0}
            venue_states[venue_id]["view_count"] = venue_states[venue_id].get("view_count", 0) + 1

            if action == "make_booking" and event.get("success"):
                venue_states[venue_id]["booking_count"] = venue_states[venue_id].get("booking_count", 0) + 1

        # Update social graph for new friendships
        if action == "respond_invite" and event.get("accepted"):
            user_id = event.get("user_id")
            friend_id = event.get("friend_id")
            if user_id and friend_id:
                if user_id not in social_graph:
                    social_graph[user_id] = []
                if friend_id not in social_graph[user_id]:
                    social_graph[user_id].append(friend_id)

    # Advance simulation time
    speed = state.get("speed_multiplier", 1.0)
    new_time = state.get("simulation_time", datetime.utcnow()) + timedelta(seconds=speed)

    return {
        "metrics": metrics,
        "venue_states": venue_states,
        "social_graph": social_graph,
        "simulation_time": new_time,
        "executed_events": [],  # Clear for next tick
        "selected_actions": {},  # Clear for next tick
    }


async def event_emitter(state: SimulationGraphState, db: AsyncSession) -> dict:
    """
    Node 5: EventEmitter

    Publishes aggregated events and metrics to streams.
    """
    logger.debug("EventEmitter: Publishing events")

    streaming = get_streaming_service()
    metrics = state.get("metrics", {})
    simulation_time = state.get("simulation_time", datetime.utcnow())

    # Publish metrics update periodically
    if metrics.get("events_generated", 0) % 5 == 0:
        await streaming.publish_event(
            event_type="metrics_update",
            channel="system_metrics",
            payload={
                "events_generated": metrics.get("events_generated", 0),
                "bookings_created": metrics.get("bookings_created", 0),
                "invites_sent": metrics.get("invites_sent", 0),
                "active_users": metrics.get("active_user_count", 0),
                "browse_count": metrics.get("browse_count", 0),
            },
            simulation_time=simulation_time
        )

    return {}


# ============================================================================
# Action Execution Helpers
# ============================================================================

async def _execute_browse(db: AsyncSession, user: User, simulation_time: datetime, streaming) -> dict:
    """Execute browse action."""
    query = select(Venue).order_by(func.random()).limit(1)
    result = await db.execute(query)
    venue = result.scalar_one_or_none()

    if venue:
        duration = random.randint(5, 60)

        await streaming.publish_event(
            event_type="user_browse",
            channel="user_actions",
            payload={
                "action": "browse_venue",
                "venue_id": venue.id,
                "venue_name": venue.name,
                "duration_seconds": duration,
            },
            simulation_time=simulation_time,
            user_id=user.id,
            venue_id=venue.id
        )

        return {
            "action": "browse",
            "venue_id": venue.id,
            "venue_name": venue.name,
        }

    return {"action": "browse", "result": "no_venues"}


async def _execute_check_friends(db: AsyncSession, user: User, simulation_time: datetime, streaming, state: dict) -> dict:
    """Execute check friends action."""
    social_graph = state.get("social_graph", {})
    friends = social_graph.get(user.id, [])

    if friends:
        friend_id = random.choice(friends)

        await streaming.publish_event(
            event_type="user_browse",
            channel="user_actions",
            payload={
                "action": "check_friends",
                "friend_id": friend_id,
            },
            simulation_time=simulation_time,
            user_id=user.id
        )

        return {"action": "check_friends", "friend_id": friend_id}

    return {"action": "check_friends", "result": "no_friends"}


async def _execute_express_interest(db: AsyncSession, user: User, simulation_time: datetime, streaming) -> dict:
    """Execute express interest action."""
    query = select(Venue).order_by(func.random()).limit(1)
    result = await db.execute(query)
    venue = result.scalar_one_or_none()

    if venue:
        time_slots = ["breakfast", "lunch", "dinner", "brunch"]
        preferred_slot = random.choice(time_slots)

        # Create interest record
        interest = VenueInterest(
            user_id=user.id,
            venue_id=venue.id,
            explicitly_interested=1,
            preferred_time_slot=preferred_slot,
            open_to_invites=random.random() > 0.3
        )
        db.add(interest)
        await db.commit()

        await streaming.publish_event(
            event_type="user_interest",
            channel="user_actions",
            payload={
                "action": "express_interest",
                "venue_id": venue.id,
                "venue_name": venue.name,
                "time_slot": preferred_slot,
            },
            simulation_time=simulation_time,
            user_id=user.id,
            venue_id=venue.id
        )

        return {
            "action": "express_interest",
            "venue_id": venue.id,
            "venue_name": venue.name,
        }

    return {"action": "express_interest", "result": "no_venue"}


async def _execute_send_invite(db: AsyncSession, user: User, simulation_time: datetime, streaming, state: dict) -> dict:
    """Execute send invite action."""
    social_graph = state.get("social_graph", {})
    friends = social_graph.get(user.id, [])

    if not friends:
        return {"action": "send_invite", "result": "no_friends"}

    friend_id = random.choice(friends)

    query = select(Venue).order_by(func.random()).limit(1)
    result = await db.execute(query)
    venue = result.scalar_one_or_none()

    if venue:
        await streaming.publish_event(
            event_type="invite_sent",
            channel="social_interactions",
            payload={
                "inviter_id": user.id,
                "invitee_id": friend_id,
                "venue_id": venue.id,
                "venue_name": venue.name,
            },
            simulation_time=simulation_time,
            user_id=user.id,
            venue_id=venue.id
        )

        return {
            "action": "send_invite",
            "invitee_id": friend_id,
            "venue_id": venue.id,
            "venue_name": venue.name,
        }

    return {"action": "send_invite", "result": "no_venue"}


async def _execute_respond_invite(db: AsyncSession, user: User, simulation_time: datetime, streaming) -> dict:
    """Execute respond to invite action."""
    accepted = random.random() > 0.3  # 70% acceptance rate

    await streaming.publish_event(
        event_type="invite_response",
        channel="social_interactions",
        payload={
            "user_id": user.id,
            "accepted": accepted,
        },
        simulation_time=simulation_time,
        user_id=user.id
    )

    return {"action": "respond_invite", "accepted": accepted}


async def _execute_make_booking(db: AsyncSession, user: User, simulation_time: datetime, streaming) -> dict:
    """Execute make booking action."""
    query = select(Venue).order_by(func.random()).limit(1)
    result = await db.execute(query)
    venue = result.scalar_one_or_none()

    if venue:
        booking_agent = BookingAgent(db)
        booking_result = await booking_agent.create_booking(
            user_id=user.id,
            venue_id=venue.id,
            party_size=random.randint(2, 4),
            preferred_time=simulation_time + timedelta(hours=random.randint(1, 48))
        )

        return {
            "action": "make_booking",
            "venue_id": venue.id,
            "venue_name": venue.name,
            "success": booking_result.get("success", False),
            "booking_id": booking_result.get("booking_id"),
        }

    return {"action": "make_booking", "result": "no_venue"}


# ============================================================================
# Graph Builder
# ============================================================================

def build_simulation_graph():
    """
    Build the LangGraph simulation state graph.

    Graph flow:
    UserPoolManager -> BehaviorEngine -> ActionExecutor -> StateUpdater -> EventEmitter
                                                                               |
                                                                               v
                                                                        (loop back or END)
    """
    # We'll create wrapper nodes that handle the db session
    # The actual nodes above need db session, so we'll handle that in the orchestrator

    workflow = StateGraph(SimulationGraphState)

    # Add placeholder nodes - actual execution happens in orchestrator
    workflow.add_node("user_pool_manager", lambda state: state)
    workflow.add_node("behavior_engine", lambda state: state)
    workflow.add_node("action_executor", lambda state: state)
    workflow.add_node("state_updater", lambda state: state)
    workflow.add_node("event_emitter", lambda state: state)

    # Define edges
    workflow.add_edge("user_pool_manager", "behavior_engine")
    workflow.add_edge("behavior_engine", "action_executor")
    workflow.add_edge("action_executor", "state_updater")
    workflow.add_edge("state_updater", "event_emitter")
    workflow.add_edge("event_emitter", END)

    # Set entry point
    workflow.set_entry_point("user_pool_manager")

    return workflow.compile()


# ============================================================================
# LangGraph Orchestrator
# ============================================================================

class LangGraphSimulationOrchestrator:
    """
    Orchestrator that uses LangGraph for simulation control flow.

    This replaces the loop-based SimulationOrchestrator with a
    graph-based approach for better state management.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.streaming = get_streaming_service()
        self.config = SimulationConfig()
        self.graph = build_simulation_graph()

        self.state: SimulationGraphState = {
            "simulation_time": datetime.utcnow(),
            "speed_multiplier": 1.0,
            "active_users": [],
            "user_pool_size": 30,
            "pending_events": [],
            "selected_actions": {},
            "executed_events": [],
            "venue_states": {},
            "social_graph": {},
            "metrics": {
                "events_generated": 0,
                "bookings_created": 0,
                "invites_sent": 0,
            },
            "scenario": "normal",
            "action_probabilities": self.config.base_action_probabilities,
            "persona_modifiers": self.config.persona_modifiers,
            "temporal_modifiers": {},
            "is_running": False,
            "is_paused": False,
            "db_session_id": "",
        }

        self._task: Optional[asyncio.Task] = None

    async def start(self, speed: float = 1.0, scenario: str = "normal") -> dict:
        """Start the simulation."""
        if self.state["is_running"]:
            return {"status": "already_running"}

        self.state["is_running"] = True
        self.state["is_paused"] = False
        self.state["speed_multiplier"] = speed
        self.state["scenario"] = scenario
        self.state["simulation_time"] = datetime.utcnow()

        # Publish start event
        await self.streaming.publish_event(
            event_type="simulation_started",
            channel="simulation_control",
            payload={
                "speed": speed,
                "scenario": scenario,
                "mode": "langgraph",
            },
            simulation_time=self.state["simulation_time"]
        )

        # Start simulation loop
        self._task = asyncio.create_task(self._run_graph_loop())

        return {
            "status": "started",
            "speed": speed,
            "scenario": scenario,
            "mode": "langgraph",
        }

    async def pause(self) -> dict:
        """Pause the simulation."""
        self.state["is_paused"] = True

        await self.streaming.publish_event(
            event_type="simulation_paused",
            channel="simulation_control",
            payload={"simulation_time": self.state["simulation_time"].isoformat()},
            simulation_time=self.state["simulation_time"]
        )

        return {"status": "paused"}

    async def resume(self) -> dict:
        """Resume the simulation."""
        self.state["is_paused"] = False

        await self.streaming.publish_event(
            event_type="simulation_resumed",
            channel="simulation_control",
            payload={"simulation_time": self.state["simulation_time"].isoformat()},
            simulation_time=self.state["simulation_time"]
        )

        return {"status": "resumed"}

    async def stop(self) -> dict:
        """Stop the simulation."""
        self.state["is_running"] = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        await self.streaming.publish_event(
            event_type="simulation_stopped",
            channel="simulation_control",
            payload={
                "events_generated": self.state["metrics"].get("events_generated", 0),
                "bookings_created": self.state["metrics"].get("bookings_created", 0),
            },
            simulation_time=self.state["simulation_time"]
        )

        return {
            "status": "stopped",
            "events_generated": self.state["metrics"].get("events_generated", 0),
            "bookings_created": self.state["metrics"].get("bookings_created", 0),
        }

    async def reset(self) -> dict:
        """Reset simulation state."""
        await self.stop()

        self.state = {
            "simulation_time": datetime.utcnow(),
            "speed_multiplier": 1.0,
            "active_users": [],
            "user_pool_size": 30,
            "pending_events": [],
            "selected_actions": {},
            "executed_events": [],
            "venue_states": {},
            "social_graph": {},
            "metrics": {
                "events_generated": 0,
                "bookings_created": 0,
                "invites_sent": 0,
            },
            "scenario": "normal",
            "action_probabilities": self.config.base_action_probabilities,
            "persona_modifiers": self.config.persona_modifiers,
            "temporal_modifiers": {},
            "is_running": False,
            "is_paused": False,
            "db_session_id": "",
        }

        await self.streaming.clear_streams()

        return {"status": "reset"}

    async def set_speed(self, multiplier: float) -> dict:
        """Set simulation speed multiplier."""
        self.state["speed_multiplier"] = multiplier
        return {"speed": multiplier}

    async def trigger_scenario(self, scenario: str) -> dict:
        """Trigger a specific scenario."""
        self.state["scenario"] = scenario

        # Update action probabilities based on scenario
        scenario_mods = self.config.scenario_modifiers.get(scenario, {})

        new_probs = self.config.base_action_probabilities.copy()
        for action, mod in scenario_mods.items():
            if action in new_probs:
                new_probs[action] *= mod

        self.state["action_probabilities"] = new_probs

        await self.streaming.publish_event(
            event_type="scenario_triggered",
            channel="simulation_control",
            payload={"scenario": scenario},
            simulation_time=self.state["simulation_time"]
        )

        return {"scenario": scenario}

    async def set_temporal_modifiers(self, modifiers: Dict[str, float]) -> dict:
        """Set temporal modifiers from TemporalEventGenerator."""
        self.state["temporal_modifiers"] = modifiers
        return {"temporal_modifiers": modifiers}

    async def get_state(self) -> dict:
        """Get current simulation state."""
        return {
            "running": self.state["is_running"],
            "paused": self.state["is_paused"],
            "simulation_time": self.state["simulation_time"].isoformat(),
            "speed_multiplier": self.state["speed_multiplier"],
            "scenario": self.state["scenario"],
            "active_users": len(self.state["active_users"]),
            "metrics": self.state["metrics"],
        }

    async def get_metrics(self) -> dict:
        """Get simulation metrics."""
        return {
            **self.state["metrics"],
            "active_users": len(self.state["active_users"]),
            "simulation_time": self.state["simulation_time"].isoformat(),
            "speed_multiplier": self.state["speed_multiplier"],
            "scenario": self.state["scenario"],
            "running": self.state["is_running"],
            "paused": self.state["is_paused"],
        }

    async def _run_graph_loop(self):
        """Main simulation loop using LangGraph nodes."""
        while self.state["is_running"]:
            if self.state["is_paused"]:
                await asyncio.sleep(0.5)
                continue

            try:
                # Execute graph nodes manually with db session
                # Node 1: UserPoolManager
                updates = await user_pool_manager(self.state, self.db)
                self.state.update(updates)

                # Node 2: BehaviorEngine
                updates = await behavior_engine(self.state, self.db)
                self.state.update(updates)

                # Node 3: ActionExecutor
                updates = await action_executor(self.state, self.db)
                self.state.update(updates)

                # Node 4: StateUpdater
                updates = await state_updater(self.state, self.db)
                self.state.update(updates)

                # Node 5: EventEmitter
                updates = await event_emitter(self.state, self.db)
                self.state.update(updates)

            except Exception as e:
                logger.error(f"Error in simulation loop: {e}")

            # Sleep based on speed
            await asyncio.sleep(1.0 / self.state["speed_multiplier"])

    async def spawn_users(self, count: int) -> dict:
        """Spawn new simulated users."""
        from ..services.data_generator import DataGenerator

        generator = DataGenerator(self.db)
        new_users = await generator.generate_users(count)

        # Add to active users
        new_ids = [u.id for u in new_users]
        self.state["active_users"].extend(new_ids)

        # Initialize social graph for new users
        for user_id in new_ids:
            self.state["social_graph"][user_id] = []

        await self.streaming.publish_event(
            event_type="users_spawned",
            channel="simulation_control",
            payload={"count": count, "user_ids": new_ids},
            simulation_time=self.state["simulation_time"]
        )

        return {"spawned": count, "user_ids": new_ids}

    async def adjust_behavior(
        self,
        persona: Optional[str] = None,
        probabilities: Optional[Dict[str, float]] = None,
        apply_global: bool = False
    ) -> dict:
        """Adjust behavior probabilities."""
        if apply_global and probabilities:
            # Update base probabilities
            for action, prob in probabilities.items():
                if action in self.state["action_probabilities"]:
                    self.state["action_probabilities"][action] = prob
        elif persona and probabilities:
            # Update persona-specific modifiers
            if persona not in self.state["persona_modifiers"]:
                self.state["persona_modifiers"][persona] = {}
            self.state["persona_modifiers"][persona].update(probabilities)

        await self.streaming.publish_event(
            event_type="behavior_adjusted",
            channel="simulation_control",
            payload={
                "persona": persona,
                "probabilities": probabilities,
                "global": apply_global,
            },
            simulation_time=self.state["simulation_time"]
        )

        return {
            "action_probabilities": self.state["action_probabilities"],
            "persona_modifiers": self.state["persona_modifiers"],
        }
