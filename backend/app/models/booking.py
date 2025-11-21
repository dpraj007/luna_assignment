"""
Booking models for Luna Social.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from ..core.database import Base


class BookingStatus(str, enum.Enum):
    """Booking status states."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"


class Booking(Base):
    """Booking model for venue reservations."""
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)

    # References
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    venue_id = Column(Integer, ForeignKey("venues.id"), nullable=False)

    # Booking details
    party_size = Column(Integer, default=2)
    booking_time = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, default=90)

    # Status
    status = Column(SQLEnum(BookingStatus), default=BookingStatus.PENDING)

    # Group booking (JSON array of user IDs who are part of this booking)
    group_members = Column(JSON, default=list)

    # Special requests
    special_requests = Column(String(500))

    # Confirmation
    confirmation_code = Column(String(20), unique=True)

    # Agent tracking (which agent created this booking)
    created_by_agent = Column(String(50))  # "booking_agent", "user", etc.

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="bookings")
    venue = relationship("Venue", back_populates="bookings")
    invitations = relationship("BookingInvitation", back_populates="booking")

    def __repr__(self):
        return f"<Booking(id={self.id}, user={self.user_id}, venue={self.venue_id})>"


class BookingInvitation(Base):
    """Invitation to join a booking/gathering."""
    __tablename__ = "booking_invitations"

    id = Column(Integer, primary_key=True, index=True)

    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=False)
    inviter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    invitee_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Status
    status = Column(String(20), default="pending")  # pending, accepted, declined

    # Message
    message = Column(String(500))

    # Response tracking
    responded_at = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    booking = relationship("Booking", back_populates="invitations")
    inviter = relationship("User", foreign_keys=[inviter_id])
    invitee = relationship("User", foreign_keys=[invitee_id])

    def __repr__(self):
        return f"<BookingInvitation(booking={self.booking_id}, invitee={self.invitee_id})>"
