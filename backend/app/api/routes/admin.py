"""
Admin Dashboard API routes.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import asyncio
import json

from ...core.database import get_db
from ...models.user import User
from ...models.venue import Venue
from ...models.booking import Booking, BookingStatus
from ...models.event import SimulationEvent
from ...services.streaming import get_streaming_service
from ...services.data_generator import DataGenerator

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
    - user_actions: User behavior events
    - recommendations: Generated recommendations
    - bookings: Booking activities
    - social: Social interactions
    - system: System events
    - metrics: Performance metrics
    - simulation: Simulation control events
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
