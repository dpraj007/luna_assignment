"""
Streaming service for real-time event distribution.
Uses Redis Streams for event bus and SSE for client delivery.
"""
import asyncio
import json
from typing import Optional, AsyncGenerator, Dict, List, Any
from datetime import datetime
from dataclasses import dataclass, asdict
import logging

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from ..core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class StreamEvent:
    """Event structure for streaming."""
    event_type: str
    channel: str
    payload: Dict[str, Any]
    simulation_time: str
    user_id: Optional[int] = None
    venue_id: Optional[int] = None
    booking_id: Optional[int] = None
    created_at: str = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class InMemoryStreamBackend:
    """In-memory stream backend for demo/testing."""

    def __init__(self):
        self.streams: Dict[str, List[StreamEvent]] = {}
        self.subscribers: Dict[str, List[asyncio.Queue]] = {}
        self.max_stream_size = 1000

    async def publish(self, channel: str, event: StreamEvent):
        """Publish event to a channel."""
        if channel not in self.streams:
            self.streams[channel] = []
            self.subscribers[channel] = []

        # Add to stream
        self.streams[channel].append(event)

        # Trim if too large
        if len(self.streams[channel]) > self.max_stream_size:
            self.streams[channel] = self.streams[channel][-self.max_stream_size:]

        # Notify subscribers
        for queue in self.subscribers[channel]:
            await queue.put(event)

    async def subscribe(self, channel: str) -> asyncio.Queue:
        """Subscribe to a channel."""
        if channel not in self.subscribers:
            self.subscribers[channel] = []
            self.streams[channel] = []

        queue = asyncio.Queue()
        self.subscribers[channel].append(queue)
        return queue

    async def unsubscribe(self, channel: str, queue: asyncio.Queue):
        """Unsubscribe from a channel."""
        if channel in self.subscribers and queue in self.subscribers[channel]:
            self.subscribers[channel].remove(queue)

    async def get_history(self, channel: str, limit: int = 100) -> List[StreamEvent]:
        """Get recent events from a channel."""
        if channel not in self.streams:
            return []
        return self.streams[channel][-limit:]

    async def clear(self, channel: Optional[str] = None):
        """Clear stream(s)."""
        if channel:
            self.streams[channel] = []
        else:
            self.streams = {}


class RedisStreamBackend:
    """Redis-based stream backend for production."""

    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis: Optional[redis.Redis] = None
        self.max_stream_size = 10000

    async def connect(self):
        """Connect to Redis."""
        if REDIS_AVAILABLE:
            self.redis = redis.from_url(self.redis_url)
        else:
            raise ImportError("redis package not available")

    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis:
            await self.redis.close()

    async def publish(self, channel: str, event: StreamEvent):
        """Publish event to Redis stream."""
        if not self.redis:
            await self.connect()

        stream_key = f"luna:stream:{channel}"
        await self.redis.xadd(
            stream_key,
            {"data": event.to_json()},
            maxlen=self.max_stream_size
        )

        # Also publish to pubsub for real-time subscribers
        await self.redis.publish(f"luna:pubsub:{channel}", event.to_json())

    async def subscribe(self, channel: str) -> AsyncGenerator[StreamEvent, None]:
        """Subscribe to Redis pubsub channel."""
        if not self.redis:
            await self.connect()

        pubsub = self.redis.pubsub()
        await pubsub.subscribe(f"luna:pubsub:{channel}")

        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(message["data"])
                    yield StreamEvent(**data)
        finally:
            await pubsub.unsubscribe(f"luna:pubsub:{channel}")

    async def get_history(self, channel: str, limit: int = 100) -> List[dict]:
        """Get recent events from Redis stream."""
        if not self.redis:
            await self.connect()

        stream_key = f"luna:stream:{channel}"
        messages = await self.redis.xrevrange(stream_key, count=limit)

        events = []
        for msg_id, data in messages:
            event_data = json.loads(data[b"data"])
            events.append(event_data)

        return list(reversed(events))


class StreamingService:
    """
    Main streaming service for Luna Social.

    Handles event publishing, subscription, and history.
    Uses in-memory backend for demo, Redis for production.
    """

    # Channel definitions (aligned with implementation plan)
    CHANNELS = {
        "user_actions": "User behavior events (browsing, searching, interests)",
        "recommendations": "Generated recommendations and compatibility scores",
        "bookings": "Booking activities (created, confirmed, cancelled)",
        "social_interactions": "Social interactions (friend requests, invites)",
        "system_metrics": "System events and performance metrics",
        "simulation_control": "Simulation control events (start, pause, scenarios)",
        "environmental": "Environmental events (weather, traffic, special events)",
    }

    def __init__(self, use_redis: bool = False):
        self.use_redis = use_redis and REDIS_AVAILABLE

        if self.use_redis:
            self.backend = RedisStreamBackend(settings.REDIS_URL)
        else:
            self.backend = InMemoryStreamBackend()

        self._metrics = {
            "events_published": 0,
            "active_subscribers": 0,
        }

    async def publish_event(
        self,
        event_type: str,
        channel: str,
        payload: dict,
        simulation_time: Optional[datetime] = None,
        user_id: Optional[int] = None,
        venue_id: Optional[int] = None,
        booking_id: Optional[int] = None
    ):
        """Publish an event to a channel."""
        event = StreamEvent(
            event_type=event_type,
            channel=channel,
            payload=payload,
            simulation_time=(simulation_time or datetime.utcnow()).isoformat(),
            user_id=user_id,
            venue_id=venue_id,
            booking_id=booking_id
        )

        await self.backend.publish(channel, event)
        self._metrics["events_published"] += 1

        logger.debug(f"Published event: {event_type} to {channel}")

    async def subscribe(self, channel: str) -> asyncio.Queue:
        """Subscribe to a channel (in-memory backend only)."""
        if isinstance(self.backend, InMemoryStreamBackend):
            self._metrics["active_subscribers"] += 1
            return await self.backend.subscribe(channel)
        raise NotImplementedError("Use subscribe_generator for Redis backend")

    async def unsubscribe(self, channel: str, queue: asyncio.Queue):
        """Unsubscribe from a channel."""
        if isinstance(self.backend, InMemoryStreamBackend):
            await self.backend.unsubscribe(channel, queue)
            self._metrics["active_subscribers"] -= 1

    async def get_history(self, channel: str, limit: int = 100) -> List[dict]:
        """Get recent events from a channel."""
        events = await self.backend.get_history(channel, limit)
        if isinstance(self.backend, InMemoryStreamBackend):
            return [e.to_dict() for e in events]
        return events

    async def sse_generator(
        self,
        channels: List[str],
        include_history: bool = False
    ) -> AsyncGenerator[str, None]:
        """
        Generate SSE events for multiple channels.

        Yields events in SSE format: "data: {json}\n\n"
        """
        if not isinstance(self.backend, InMemoryStreamBackend):
            raise NotImplementedError("SSE generator only works with in-memory backend")

        # Subscribe to all channels
        queues = {}
        for channel in channels:
            queues[channel] = await self.subscribe(channel)

        try:
            # Send history if requested
            if include_history:
                for channel in channels:
                    history = await self.get_history(channel, limit=50)
                    for event in history:
                        yield f"data: {json.dumps(event)}\n\n"

            # Stream live events
            while True:
                # Check all queues with timeout
                for channel, queue in queues.items():
                    try:
                        event = queue.get_nowait()
                        yield f"data: {event.to_json()}\n\n"
                    except asyncio.QueueEmpty:
                        pass

                await asyncio.sleep(0.1)  # Small delay to prevent busy loop

        finally:
            # Unsubscribe from all channels
            for channel, queue in queues.items():
                await self.unsubscribe(channel, queue)

    async def clear_streams(self, channel: Optional[str] = None):
        """Clear stream data."""
        await self.backend.clear(channel)

    def get_metrics(self) -> dict:
        """Get streaming metrics."""
        return {
            **self._metrics,
            "channels": list(self.CHANNELS.keys()),
        }


# Singleton instance
_streaming_service: Optional[StreamingService] = None


def get_streaming_service() -> StreamingService:
    """Get the singleton streaming service instance."""
    global _streaming_service
    if _streaming_service is None:
        _streaming_service = StreamingService(use_redis=not settings.USE_FAKE_REDIS)
    return _streaming_service
