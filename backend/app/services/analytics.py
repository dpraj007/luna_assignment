"""
Analytics, Monitoring & Debugging Services.

Provides:
- Event replay capability
- User journey tracking
- State snapshot/restore
- Metrics aggregation
"""
from typing import Dict, Any, Optional, List, AsyncGenerator
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import asyncio
import json
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from ..models.event import SimulationEvent, EventType
from ..models.user import User
from ..models.booking import Booking
from ..services.streaming import get_streaming_service, StreamEvent

logger = logging.getLogger(__name__)


# ============================================================================
# Event Replay Service
# ============================================================================

class EventReplayService:
    """
    Service for replaying historical events.

    Allows replaying events from the database at various speeds
    for debugging and demonstration purposes.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.streaming = get_streaming_service()
        self._replay_task: Optional[asyncio.Task] = None
        self._is_replaying = False

    async def replay_events(
        self,
        start_time: datetime,
        end_time: datetime,
        speed_multiplier: float = 1.0,
        channels: Optional[List[str]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Replay events from a time range.

        Args:
            start_time: Start of replay window
            end_time: End of replay window
            speed_multiplier: Speed of replay (1.0 = realtime)
            channels: Optional list of channels to replay

        Yields:
            Event dictionaries
        """
        self._is_replaying = True

        try:
            # Build query
            query = select(SimulationEvent).where(
                and_(
                    SimulationEvent.simulation_time >= start_time,
                    SimulationEvent.simulation_time <= end_time
                )
            ).order_by(SimulationEvent.simulation_time)

            if channels:
                query = query.where(SimulationEvent.channel.in_(channels))

            result = await self.db.execute(query)
            events = result.scalars().all()

            if not events:
                yield {"type": "replay_complete", "message": "No events found"}
                return

            logger.info(f"Replaying {len(events)} events from {start_time} to {end_time}")

            # Replay events with timing
            last_time = None
            for event in events:
                if not self._is_replaying:
                    break

                # Calculate delay
                if last_time:
                    time_diff = (event.simulation_time - last_time).total_seconds()
                    delay = time_diff / speed_multiplier
                    if delay > 0:
                        await asyncio.sleep(min(delay, 5.0))  # Cap delay at 5 seconds

                last_time = event.simulation_time

                # Yield event
                event_data = event.to_dict()
                event_data["_replay"] = True
                yield event_data

                # Re-publish to stream
                await self.streaming.publish_event(
                    event_type=f"replay_{event.event_type.value}",
                    channel=event.channel,
                    payload={**event.payload, "_replay": True},
                    simulation_time=event.simulation_time,
                    user_id=event.user_id,
                    venue_id=event.venue_id
                )

            yield {"type": "replay_complete", "events_replayed": len(events)}

        finally:
            self._is_replaying = False

    async def stop_replay(self):
        """Stop ongoing replay."""
        self._is_replaying = False
        if self._replay_task:
            self._replay_task.cancel()

    async def get_replay_summary(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """Get summary of events in a time range."""
        query = select(
            SimulationEvent.channel,
            func.count(SimulationEvent.id).label("count")
        ).where(
            and_(
                SimulationEvent.simulation_time >= start_time,
                SimulationEvent.simulation_time <= end_time
            )
        ).group_by(SimulationEvent.channel)

        result = await self.db.execute(query)
        by_channel = {row.channel: row.count for row in result}

        total_query = select(func.count(SimulationEvent.id)).where(
            and_(
                SimulationEvent.simulation_time >= start_time,
                SimulationEvent.simulation_time <= end_time
            )
        )
        total_result = await self.db.execute(total_query)
        total = total_result.scalar() or 0

        return {
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "total_events": total,
            "by_channel": by_channel,
        }


# ============================================================================
# User Journey Tracking Service
# ============================================================================

@dataclass
class JourneyMilestone:
    """A milestone in a user's journey."""
    type: str
    timestamp: datetime
    event_id: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class UserJourneyService:
    """
    Service for tracking and analyzing user journeys.

    Tracks user events and identifies key milestones in their journey.
    """

    # Milestone definitions
    MILESTONES = [
        "first_browse",
        "first_interest",
        "first_invite_sent",
        "first_invite_received",
        "first_booking",
        "first_completed_booking",
        "reached_5_friends",
        "reached_10_bookings",
    ]

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_journey(
        self,
        user_id: int,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get a user's journey with events and milestones.

        Args:
            user_id: The user ID
            start_time: Optional start of time range
            end_time: Optional end of time range
            limit: Max events to return

        Returns:
            Dict with events, milestones, and summary
        """
        # Build query
        query = select(SimulationEvent).where(
            SimulationEvent.user_id == user_id
        ).order_by(SimulationEvent.simulation_time)

        if start_time:
            query = query.where(SimulationEvent.simulation_time >= start_time)
        if end_time:
            query = query.where(SimulationEvent.simulation_time <= end_time)

        query = query.limit(limit)

        result = await self.db.execute(query)
        events = result.scalars().all()

        # Extract milestones
        milestones = await self._extract_milestones(user_id, events)

        # Build summary
        summary = await self._build_journey_summary(user_id, events)

        return {
            "user_id": user_id,
            "events": [e.to_dict() for e in events],
            "milestones": [asdict(m) for m in milestones],
            "summary": summary,
        }

    async def _extract_milestones(
        self,
        user_id: int,
        events: List[SimulationEvent]
    ) -> List[JourneyMilestone]:
        """Extract milestones from events."""
        milestones = []
        seen_types = set()

        for event in events:
            event_type = event.event_type.value if event.event_type else ""

            # First browse
            if "browse" in event_type and "first_browse" not in seen_types:
                milestones.append(JourneyMilestone(
                    type="first_browse",
                    timestamp=event.simulation_time,
                    event_id=event.id,
                ))
                seen_types.add("first_browse")

            # First interest
            if "interest" in event_type and "first_interest" not in seen_types:
                milestones.append(JourneyMilestone(
                    type="first_interest",
                    timestamp=event.simulation_time,
                    event_id=event.id,
                ))
                seen_types.add("first_interest")

            # First invite sent
            if "invite_sent" in event_type and "first_invite_sent" not in seen_types:
                milestones.append(JourneyMilestone(
                    type="first_invite_sent",
                    timestamp=event.simulation_time,
                    event_id=event.id,
                ))
                seen_types.add("first_invite_sent")

            # First booking
            if "booking_created" in event_type and "first_booking" not in seen_types:
                milestones.append(JourneyMilestone(
                    type="first_booking",
                    timestamp=event.simulation_time,
                    event_id=event.id,
                ))
                seen_types.add("first_booking")

        return milestones

    async def _build_journey_summary(
        self,
        user_id: int,
        events: List[SimulationEvent]
    ) -> Dict[str, Any]:
        """Build summary statistics for user journey."""
        if not events:
            return {
                "total_events": 0,
                "duration_hours": 0,
            }

        event_counts = {}
        for event in events:
            event_type = event.event_type.value if event.event_type else "unknown"
            event_counts[event_type] = event_counts.get(event_type, 0) + 1

        duration = (events[-1].simulation_time - events[0].simulation_time).total_seconds() / 3600

        return {
            "total_events": len(events),
            "duration_hours": round(duration, 2),
            "event_counts": event_counts,
            "first_event": events[0].simulation_time.isoformat(),
            "last_event": events[-1].simulation_time.isoformat(),
        }


# ============================================================================
# State Snapshot Service
# ============================================================================

@dataclass
class SimulationSnapshot:
    """A snapshot of simulation state."""
    id: int
    name: str
    description: str
    simulation_time: datetime
    state_data: Dict[str, Any]
    created_at: datetime


class SnapshotService:
    """
    Service for creating and restoring simulation state snapshots.

    Allows saving current simulation state and restoring it later
    for debugging and testing.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self._snapshots: Dict[int, SimulationSnapshot] = {}
        self._next_id = 1

    async def create_snapshot(
        self,
        name: str,
        description: str,
        state: Dict[str, Any]
    ) -> SimulationSnapshot:
        """
        Create a new state snapshot.

        Args:
            name: Name for the snapshot
            description: Description of the snapshot
            state: Current simulation state

        Returns:
            Created snapshot
        """
        snapshot = SimulationSnapshot(
            id=self._next_id,
            name=name,
            description=description,
            simulation_time=datetime.fromisoformat(
                state.get("simulation_time", datetime.utcnow().isoformat())
            ),
            state_data=state,
            created_at=datetime.utcnow(),
        )

        self._snapshots[self._next_id] = snapshot
        self._next_id += 1

        logger.info(f"Created snapshot '{name}' with ID {snapshot.id}")

        return snapshot

    async def restore_snapshot(self, snapshot_id: int) -> Optional[Dict[str, Any]]:
        """
        Restore a snapshot.

        Args:
            snapshot_id: ID of snapshot to restore

        Returns:
            Restored state data or None if not found
        """
        snapshot = self._snapshots.get(snapshot_id)
        if not snapshot:
            logger.warning(f"Snapshot {snapshot_id} not found")
            return None

        logger.info(f"Restoring snapshot '{snapshot.name}'")
        return snapshot.state_data

    async def list_snapshots(self) -> List[Dict[str, Any]]:
        """List all available snapshots."""
        return [
            {
                "id": s.id,
                "name": s.name,
                "description": s.description,
                "simulation_time": s.simulation_time.isoformat(),
                "created_at": s.created_at.isoformat(),
            }
            for s in self._snapshots.values()
        ]

    async def delete_snapshot(self, snapshot_id: int) -> bool:
        """Delete a snapshot."""
        if snapshot_id in self._snapshots:
            del self._snapshots[snapshot_id]
            logger.info(f"Deleted snapshot {snapshot_id}")
            return True
        return False


# ============================================================================
# Metrics Aggregation Service
# ============================================================================

class MetricsAggregationService:
    """
    Service for aggregating and analyzing metrics.

    Provides time-series aggregation of events and metrics.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def aggregate_events(
        self,
        time_range: timedelta,
        bucket_size: timedelta,
        event_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Aggregate events into time buckets.

        Args:
            time_range: How far back to look
            bucket_size: Size of each time bucket
            event_types: Optional filter for event types

        Returns:
            Aggregated metrics
        """
        end_time = datetime.utcnow()
        start_time = end_time - time_range

        # Get all events in range
        query = select(SimulationEvent).where(
            SimulationEvent.simulation_time >= start_time
        ).order_by(SimulationEvent.simulation_time)

        if event_types:
            query = query.where(
                SimulationEvent.event_type.in_([
                    EventType(t) for t in event_types if t in EventType.__members__
                ])
            )

        result = await self.db.execute(query)
        events = result.scalars().all()

        # Build time buckets
        buckets = []
        current = start_time
        while current < end_time:
            bucket_end = current + bucket_size
            bucket_events = [
                e for e in events
                if current <= e.simulation_time < bucket_end
            ]

            buckets.append({
                "start": current.isoformat(),
                "end": bucket_end.isoformat(),
                "count": len(bucket_events),
                "by_type": self._count_by_type(bucket_events),
            })

            current = bucket_end

        return {
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
            },
            "bucket_size_seconds": bucket_size.total_seconds(),
            "total_events": len(events),
            "buckets": buckets,
        }

    def _count_by_type(self, events: List[SimulationEvent]) -> Dict[str, int]:
        """Count events by type."""
        counts = {}
        for event in events:
            event_type = event.event_type.value if event.event_type else "unknown"
            counts[event_type] = counts.get(event_type, 0) + 1
        return counts

    async def get_conversion_funnel(
        self,
        time_range: timedelta
    ) -> Dict[str, Any]:
        """
        Get conversion funnel metrics.

        Tracks: Browse -> Interest -> Invite -> Booking
        """
        end_time = datetime.utcnow()
        start_time = end_time - time_range

        # Count each stage
        stages = {
            "browse": ["user_browse"],
            "interest": ["user_interest"],
            "invite": ["invite_sent"],
            "booking": ["booking_created", "booking_confirmed"],
        }

        funnel = {}
        for stage, event_types in stages.items():
            query = select(func.count(SimulationEvent.id)).where(
                and_(
                    SimulationEvent.simulation_time >= start_time,
                    SimulationEvent.event_type.in_([
                        EventType(t) for t in event_types
                        if t in EventType.__members__
                    ])
                )
            )
            result = await self.db.execute(query)
            funnel[stage] = result.scalar() or 0

        # Calculate conversion rates
        conversion_rates = {}
        prev_count = None
        for stage, count in funnel.items():
            if prev_count is not None and prev_count > 0:
                conversion_rates[f"{list(funnel.keys())[list(funnel.values()).index(prev_count)]}_to_{stage}"] = \
                    round(count / prev_count * 100, 2)
            prev_count = count

        return {
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
            },
            "funnel": funnel,
            "conversion_rates": conversion_rates,
        }
