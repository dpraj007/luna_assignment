"""
Admin Dashboard API routes.

Provides endpoints for:
- Dashboard statistics
- Event stream subscriptions (SSE)
- Simulation control (spawn users, trigger events, adjust behavior)
- Metrics (realtime and aggregate)
- Data management (seed, reset)
- Environment context
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query, Body, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import asyncio
import json
import logging

from ...core.database import get_db
from ...models.user import User, UserPersona
from ...models.venue import Venue
from ...models.booking import Booking, BookingStatus
from ...models.event import SimulationEvent
from ...services.streaming import get_streaming_service
from ...services.data_generator import DataGenerator
from ...services.temporal import get_temporal_generator
from ...services.environment import get_environment_service
from ...services.llm_client import get_llm_client, LLMClientError
from ...core.config import settings

logger = logging.getLogger(__name__)


# ============================================================================
# Pydantic Models for Request/Response
# ============================================================================

class TriggerEventRequest(BaseModel):
    """Request to trigger a custom event."""
    event_type: str
    channel: str
    payload: Dict[str, Any] = {}
    user_id: Optional[int] = None
    venue_id: Optional[int] = None
    simulation_time: Optional[datetime] = None


class AdjustBehaviorRequest(BaseModel):
    """Request to adjust simulation behavior."""
    persona: Optional[str] = None
    scenario: Optional[str] = None
    action_probabilities: Optional[Dict[str, float]] = None
    apply_global: bool = False


class WebSocketMessage(BaseModel):
    """WebSocket message structure."""
    type: str
    payload: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None

router = APIRouter()


@router.get("/stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """Get overall dashboard statistics."""
    # User counts
    user_count = await db.execute(select(func.count(User.id)))
    total_users = user_count.scalar()

    simulated_count = await db.execute(
        select(func.count(User.id)).where(User.is_simulated == True)
    )
    simulated_users = simulated_count.scalar()

    # Venue counts
    venue_count = await db.execute(select(func.count(Venue.id)))
    total_venues = venue_count.scalar()

    trending_count = await db.execute(
        select(func.count(Venue.id)).where(Venue.trending == True)
    )
    trending_venues = trending_count.scalar()

    # Booking counts
    booking_count = await db.execute(select(func.count(Booking.id)))
    total_bookings = booking_count.scalar()

    confirmed_count = await db.execute(
        select(func.count(Booking.id)).where(Booking.status == BookingStatus.CONFIRMED)
    )
    confirmed_bookings = confirmed_count.scalar()

    return {
        "users": {
            "total": total_users,
            "simulated": simulated_users,
            "real": total_users - simulated_users
        },
        "venues": {
            "total": total_venues,
            "trending": trending_venues
        },
        "bookings": {
            "total": total_bookings,
            "confirmed": confirmed_bookings
        }
    }


@router.get("/streams/subscribe/{channel}")
async def subscribe_to_stream(
    channel: str,
    include_history: bool = Query(False)
):
    """
    Subscribe to a real-time event stream via SSE.

    Available channels:
    - user_actions: User behavior events (browsing, searching, interests)
    - recommendations: Generated recommendations and compatibility scores
    - bookings: Booking activities (created, confirmed, cancelled)
    - social_interactions: Social interactions (friend requests, invites)
    - system_metrics: System events and performance metrics
    - simulation_control: Simulation control events (start, pause, scenarios)
    - environmental: Environmental events (weather, traffic, special events)
    """
    streaming = get_streaming_service()

    async def event_generator():
        queue = await streaming.subscribe(channel)

        try:
            # Send initial connection event
            yield f"data: {json.dumps({'type': 'connected', 'channel': channel})}\n\n"

            # Send history if requested
            if include_history:
                history = await streaming.get_history(channel, limit=50)
                for event in history:
                    yield f"data: {json.dumps(event)}\n\n"

            # Stream live events
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30)
                    yield f"data: {event.to_json()}\n\n"
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield f": keepalive\n\n"

        finally:
            await streaming.unsubscribe(channel, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/streams/subscribe-all")
async def subscribe_to_all_streams(include_history: bool = Query(False)):
    """Subscribe to all event streams via SSE."""
    streaming = get_streaming_service()
    channels = list(streaming.CHANNELS.keys())

    async def event_generator():
        queues = {}
        for channel in channels:
            queues[channel] = await streaming.subscribe(channel)

        try:
            # Send initial connection event
            yield f"data: {json.dumps({'type': 'connected', 'channels': channels})}\n\n"

            # Send history if requested
            if include_history:
                for channel in channels:
                    history = await streaming.get_history(channel, limit=20)
                    for event in history:
                        yield f"data: {json.dumps(event)}\n\n"

            # Stream live events from all channels
            while True:
                has_events = False
                for channel, queue in queues.items():
                    try:
                        event = queue.get_nowait()
                        yield f"data: {event.to_json()}\n\n"
                        has_events = True
                    except asyncio.QueueEmpty:
                        pass

                if not has_events:
                    await asyncio.sleep(0.1)

                # Periodic keepalive
                yield f": keepalive\n\n"
                await asyncio.sleep(1)

        finally:
            for channel, queue in queues.items():
                await streaming.unsubscribe(channel, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/streams/history/{channel}")
async def get_stream_history(
    channel: str,
    limit: int = Query(100, le=500)
):
    """Get historical events from a stream."""
    streaming = get_streaming_service()
    history = await streaming.get_history(channel, limit=limit)
    return {"channel": channel, "events": history, "count": len(history)}


@router.get("/streams/channels")
async def list_stream_channels():
    """List available stream channels."""
    streaming = get_streaming_service()
    return {"channels": streaming.CHANNELS}


@router.post("/data/seed")
async def seed_demo_data(
    user_count: int = Query(50, ge=10, le=200),
    db: AsyncSession = Depends(get_db)
):
    """Seed the database with demo data."""
    generator = DataGenerator(db)
    result = await generator.seed_all(user_count=user_count)
    return {"success": True, "seeded": result}


@router.post("/data/reset")
async def reset_data(db: AsyncSession = Depends(get_db)):
    """Reset all data (clear database)."""
    from ...core.database import drop_db, init_db

    await drop_db()
    await init_db()

    return {"success": True, "message": "Database reset complete"}


@router.get("/metrics/streaming")
async def get_streaming_metrics():
    """Get streaming service metrics."""
    streaming = get_streaming_service()
    return streaming.get_metrics()


# ============================================================================
# Control Endpoints - User Spawning, Event Triggering, Behavior Adjustment
# ============================================================================

@router.post("/control/users/spawn/{count}")
async def spawn_users(
    count: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Spawn new simulated users.

    Creates {count} new simulated users with random personas and preferences.
    Returns the list of created user IDs.
    """
    if count < 1 or count > 100:
        return {"error": "Count must be between 1 and 100"}

    generator = DataGenerator(db)
    new_users = await generator.generate_users(count)
    new_ids = [u.id for u in new_users]

    # Publish event
    streaming = get_streaming_service()
    await streaming.publish_event(
        event_type="users_spawned",
        channel="simulation_control",
        payload={"count": count, "user_ids": new_ids},
        simulation_time=datetime.utcnow()
    )

    # Get total count
    total_count = await db.execute(select(func.count(User.id)))
    total = total_count.scalar()

    return {
        "success": True,
        "spawned": count,
        "user_ids": new_ids,
        "total_users": total
    }


@router.post("/control/events/trigger")
async def trigger_event(
    request: TriggerEventRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger a custom event.

    Publishes a custom event to the specified channel.
    """
    streaming = get_streaming_service()

    # Validate channel
    if request.channel not in streaming.CHANNELS:
        return {
            "error": f"Invalid channel: {request.channel}",
            "valid_channels": list(streaming.CHANNELS.keys())
        }

    simulation_time = request.simulation_time or datetime.utcnow()

    await streaming.publish_event(
        event_type=request.event_type,
        channel=request.channel,
        payload=request.payload,
        simulation_time=simulation_time,
        user_id=request.user_id,
        venue_id=request.venue_id
    )

    return {
        "success": True,
        "event_type": request.event_type,
        "channel": request.channel
    }


@router.post("/control/behavior/adjust")
async def adjust_behavior(
    request: AdjustBehaviorRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Adjust simulation behavior probabilities.

    Can adjust:
    - Global action probabilities (apply_global=True)
    - Persona-specific modifiers
    - Scenario-specific settings
    """
    streaming = get_streaming_service()

    # This would normally update the simulation orchestrator
    # For now, we just publish the adjustment event

    await streaming.publish_event(
        event_type="behavior_adjusted",
        channel="simulation_control",
        payload={
            "persona": request.persona,
            "scenario": request.scenario,
            "probabilities": request.action_probabilities,
            "global": request.apply_global,
        },
        simulation_time=datetime.utcnow()
    )

    return {
        "success": True,
        "adjustment": {
            "persona": request.persona,
            "scenario": request.scenario,
            "probabilities": request.action_probabilities,
            "global": request.apply_global,
        }
    }


# ============================================================================
# Metrics Endpoints - Realtime and Aggregate
# ============================================================================

@router.get("/metrics/realtime")
async def get_realtime_metrics():
    """
    Get real-time metrics as SSE stream.

    Subscribes to system_metrics channel and streams updates.
    """
    streaming = get_streaming_service()

    async def metrics_generator():
        queue = await streaming.subscribe("system_metrics")

        try:
            # Send initial metrics
            yield f"data: {json.dumps({'type': 'connected', 'channel': 'system_metrics'})}\n\n"

            # Stream live metrics
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30)
                    yield f"data: {event.to_json()}\n\n"
                except asyncio.TimeoutError:
                    yield f": keepalive\n\n"

        finally:
            await streaming.unsubscribe("system_metrics", queue)

    return StreamingResponse(
        metrics_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.get("/metrics/aggregate")
async def get_aggregate_metrics(
    time_range: str = Query("24h", regex="^(1h|24h|7d|30d)$"),
    group_by: str = Query("hour", regex="^(minute|hour|day)$"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get aggregated metrics over a time range.

    - time_range: "1h", "24h", "7d", "30d"
    - group_by: "minute", "hour", "day"
    """
    # Calculate time range
    now = datetime.utcnow()
    ranges = {
        "1h": timedelta(hours=1),
        "24h": timedelta(hours=24),
        "7d": timedelta(days=7),
        "30d": timedelta(days=30),
    }
    start_time = now - ranges[time_range]

    # Get booking counts
    booking_query = select(
        func.count(Booking.id).label("count")
    ).where(Booking.created_at >= start_time)
    booking_result = await db.execute(booking_query)
    total_bookings = booking_result.scalar() or 0

    # Get user activity (simplified - would normally aggregate events)
    user_query = select(func.count(User.id)).where(User.is_simulated == True)
    user_result = await db.execute(user_query)
    total_simulated_users = user_result.scalar() or 0

    # Get venue stats
    venue_query = select(func.count(Venue.id))
    venue_result = await db.execute(venue_query)
    total_venues = venue_result.scalar() or 0

    trending_query = select(func.count(Venue.id)).where(Venue.trending == True)
    trending_result = await db.execute(trending_query)
    trending_venues = trending_result.scalar() or 0

    return {
        "time_range": time_range,
        "group_by": group_by,
        "start_time": start_time.isoformat(),
        "end_time": now.isoformat(),
        "metrics": {
            "bookings": {
                "total": total_bookings,
                "rate_per_hour": total_bookings / (ranges[time_range].total_seconds() / 3600),
            },
            "users": {
                "simulated": total_simulated_users,
            },
            "venues": {
                "total": total_venues,
                "trending": trending_venues,
            },
        }
    }


# ============================================================================
# Environment Endpoints
# ============================================================================

@router.get("/environment/context")
async def get_environment_context(
    lat: float = Query(40.7128, description="Latitude"),
    lon: float = Query(-74.0060, description="Longitude"),
    time: Optional[datetime] = None
):
    """
    Get current environment context (weather, traffic, events).
    """
    env_service = get_environment_service()
    location = {"lat": lat, "lon": lon}
    sim_time = time or datetime.utcnow()

    context = env_service.get_environment_context(location, sim_time)

    return context


@router.get("/environment/temporal")
async def get_temporal_context(time: Optional[datetime] = None):
    """
    Get temporal context (time of day, meal period, weekend, holiday).
    """
    temporal = get_temporal_generator()
    sim_time = time or datetime.utcnow()

    context = temporal.get_time_context(sim_time)
    modifiers = temporal.get_action_modifiers(context)
    scenarios = temporal.get_recommended_scenarios(context)

    return {
        "context": {
            "hour": context.hour,
            "day_of_week": context.day_of_week,
            "meal_period": context.meal_period,
            "is_weekend": context.is_weekend,
            "is_holiday": context.is_holiday,
            "holiday_name": context.holiday_name,
            "season": context.season,
        },
        "modifiers": modifiers,
        "recommended_scenarios": scenarios,
    }


# ============================================================================
# WebSocket Endpoint for Bidirectional Control
# ============================================================================

# WebSocket connection manager
class ConnectionManager:
    """Manages WebSocket connections."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting: {e}")


ws_manager = ConnectionManager()


@router.websocket("/control/ws")
async def websocket_control(websocket: WebSocket, db: AsyncSession = Depends(get_db)):
    """
    WebSocket endpoint for bidirectional admin control.

    Supports messages:
    - set_speed: {"type": "set_speed", "payload": {"multiplier": 5.0}}
    - set_scenario: {"type": "set_scenario", "payload": {"scenario": "lunch_rush"}}
    - spawn_users: {"type": "spawn_users", "payload": {"count": 10}}
    - adjust_behavior: {"type": "adjust_behavior", "payload": {...}}
    - pause: {"type": "pause"}
    - resume: {"type": "resume"}
    - get_state: {"type": "get_state"}
    """
    await ws_manager.connect(websocket)

    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            msg_type = data.get("type")
            payload = data.get("payload", {})
            request_id = data.get("request_id")

            response = {"type": "ack", "request_id": request_id, "success": True}

            try:
                if msg_type == "set_speed":
                    multiplier = payload.get("multiplier", 1.0)
                    response["data"] = {"speed": multiplier}

                elif msg_type == "set_scenario":
                    scenario = payload.get("scenario", "normal")
                    response["data"] = {"scenario": scenario}

                elif msg_type == "spawn_users":
                    count = min(100, max(1, payload.get("count", 10)))
                    generator = DataGenerator(db)
                    new_users = await generator.generate_users(count)
                    response["data"] = {
                        "spawned": count,
                        "user_ids": [u.id for u in new_users]
                    }

                elif msg_type == "adjust_behavior":
                    response["data"] = {"adjusted": payload}

                elif msg_type == "pause":
                    response["data"] = {"status": "paused"}

                elif msg_type == "resume":
                    response["data"] = {"status": "resumed"}

                elif msg_type == "get_state":
                    streaming = get_streaming_service()
                    response["data"] = {
                        "streaming_metrics": streaming.get_metrics(),
                    }

                else:
                    response["success"] = False
                    response["error"] = f"Unknown message type: {msg_type}"

            except Exception as e:
                response["success"] = False
                response["error"] = str(e)
                logger.error(f"WebSocket error handling {msg_type}: {e}")

            # Send response
            await websocket.send_json(response)

            # Broadcast state update to all clients
            if response["success"] and msg_type != "get_state":
                await ws_manager.broadcast({
                    "type": "state_update",
                    "data": response.get("data", {}),
                    "triggered_by": msg_type,
                })

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)


# ============================================================================
# LLM Status & Testing (OpenRouter API)
# ============================================================================

@router.get("/llm/status")
async def get_llm_status():
    """
    Get LLM (OpenRouter) configuration status.

    Returns whether OpenRouter is configured and ready to use,
    along with current settings.
    """
    llm_client = get_llm_client()

    return {
        "configured": llm_client.is_configured,
        "provider": "OpenRouter",
        "base_url": settings.OPENROUTER_BASE_URL,
        "model": settings.OPENROUTER_MODEL,
        "site_name": settings.OPENROUTER_SITE_NAME,
        "settings": {
            "max_tokens": settings.LLM_MAX_TOKENS,
            "temperature": settings.LLM_TEMPERATURE,
            "timeout_seconds": settings.LLM_TIMEOUT_SECONDS,
        },
        "docs_url": "https://openrouter.ai/docs",
        "models_url": "https://openrouter.ai/models",
    }


@router.post("/llm/test")
async def test_llm_connection(
    prompt: str = Body(default="Hello! Please respond with a brief greeting.", embed=True)
):
    """
    Test the LLM connection by sending a simple prompt.

    Returns the LLM response if successful, or error details if not.
    """
    llm_client = get_llm_client()

    if not llm_client.is_configured:
        return {
            "success": False,
            "error": "OpenRouter API key not configured",
            "help": "Set OPENROUTER_API_KEY in your .env file. Get your key at: https://openrouter.ai/keys"
        }

    try:
        response = await llm_client.complete(
            prompt=prompt,
            system_prompt="You are a friendly assistant. Respond briefly."
        )

        return {
            "success": True,
            "response": response.content,
            "model": response.model,
            "usage": response.usage,
            "finish_reason": response.finish_reason,
        }

    except LLMClientError as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
        }
    except Exception as e:
        logger.error(f"Unexpected LLM test error: {e}")
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
        }
