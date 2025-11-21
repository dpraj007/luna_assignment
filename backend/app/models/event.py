"""
Simulation event models for streaming.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Enum as SQLEnum
from datetime import datetime
import enum
from ..core.database import Base


class EventType(str, enum.Enum):
    """Types of simulation events."""
    # User actions
    USER_CREATED = "user_created"
    USER_ACTIVE = "user_active"
    USER_BROWSE = "user_browse"
    USER_SEARCH = "user_search"
    USER_INTEREST = "user_interest"

    # Social events
    FRIEND_REQUEST = "friend_request"
    FRIEND_ACCEPTED = "friend_accepted"
    INVITE_SENT = "invite_sent"
    INVITE_RESPONSE = "invite_response"

    # Booking events
    BOOKING_CREATED = "booking_created"
    BOOKING_CONFIRMED = "booking_confirmed"
    BOOKING_CANCELLED = "booking_cancelled"
    BOOKING_COMPLETED = "booking_completed"

    # Recommendation events
    RECOMMENDATION_GENERATED = "recommendation_generated"
    COMPATIBILITY_CALCULATED = "compatibility_calculated"

    # System events
    SIMULATION_STARTED = "simulation_started"
    SIMULATION_PAUSED = "simulation_paused"
    SIMULATION_RESUMED = "simulation_resumed"
    SIMULATION_RESET = "simulation_reset"
    SCENARIO_TRIGGERED = "scenario_triggered"

    # Venue events
    VENUE_TRENDING = "venue_trending"
    VENUE_AVAILABILITY_CHANGE = "venue_availability_change"


class SimulationEvent(Base):
    """Events generated during simulation for streaming."""
    __tablename__ = "simulation_events"

    id = Column(Integer, primary_key=True, index=True)

    # Event identification
    event_type = Column(SQLEnum(EventType), nullable=False, index=True)
    channel = Column(String(50), index=True)  # Stream channel name

    # Event data
    payload = Column(JSON, default=dict)

    # References (optional)
    user_id = Column(Integer, nullable=True)
    venue_id = Column(Integer, nullable=True)
    booking_id = Column(Integer, nullable=True)

    # Simulation time (may differ from real time)
    simulation_time = Column(DateTime, nullable=False)

    # Real timestamp
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<SimulationEvent(type={self.event_type}, time={self.simulation_time})>"

    def to_dict(self) -> dict:
        """Convert event to dictionary for streaming."""
        return {
            "id": self.id,
            "event_type": self.event_type.value,
            "channel": self.channel,
            "payload": self.payload,
            "user_id": self.user_id,
            "venue_id": self.venue_id,
            "booking_id": self.booking_id,
            "simulation_time": self.simulation_time.isoformat() if self.simulation_time else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
