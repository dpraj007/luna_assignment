"""
User interaction models for tracking behavior.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from ..core.database import Base


class InteractionType(str, enum.Enum):
    """Types of user interactions."""
    VIEW = "view"                    # Viewed a venue
    SEARCH = "search"                # Searched for venues
    SAVE = "save"                    # Saved/bookmarked venue
    SHARE = "share"                  # Shared a venue
    REVIEW = "review"                # Wrote a review
    LIKE = "like"                    # Liked a venue/review
    INVITE_SENT = "invite_sent"      # Sent an invitation
    INVITE_RECEIVED = "invite_received"
    INVITE_ACCEPTED = "invite_accepted"
    INVITE_DECLINED = "invite_declined"
    FRIEND_REQUEST = "friend_request"
    PROFILE_VIEW = "profile_view"    # Viewed another user's profile
    APP_OPEN = "app_open"            # Opened the app
    BROWSE = "browse"                # General browsing


class UserInteraction(Base):
    """Track user interactions for recommendation learning."""
    __tablename__ = "user_interactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Interaction type
    interaction_type = Column(SQLEnum(InteractionType), nullable=False)

    # Optional references
    venue_id = Column(Integer, ForeignKey("venues.id"), nullable=True)
    target_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Interaction details
    duration_seconds = Column(Integer)  # Time spent (for views)
    interaction_metadata = Column(JSON, default=dict)  # Additional context (renamed from 'metadata' which is reserved)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<UserInteraction(user={self.user_id}, type={self.interaction_type})>"


class VenueInterest(Base):
    """Track user interest in venues (for social matching)."""
    __tablename__ = "venue_interests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    venue_id = Column(Integer, ForeignKey("venues.id"), nullable=False)

    # Interest level (0-1)
    interest_score = Column(Float, default=0.5)

    # Expressed interest (user explicitly said they want to go)
    explicitly_interested = Column(Integer, default=0)  # Boolean as int for SQLite

    # Preferred time
    preferred_date = Column(DateTime, nullable=True)
    preferred_time_slot = Column(String(20))  # "lunch", "dinner", "brunch"

    # Open to invites
    open_to_invites = Column(Integer, default=1)  # Boolean as int

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="interests")
    venue = relationship("Venue", back_populates="interests")

    def __repr__(self):
        return f"<VenueInterest(user={self.user_id}, venue={self.venue_id})>"
