"""
User models for Luna Social.
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from ..core.database import Base


class UserPersona(str, enum.Enum):
    """User behavior archetypes for simulation."""
    SOCIAL_BUTTERFLY = "social_butterfly"  # High activity, many friends
    FOODIE_EXPLORER = "foodie_explorer"    # Tries new venues, writes reviews
    ROUTINE_REGULAR = "routine_regular"    # Consistent patterns
    EVENT_ORGANIZER = "event_organizer"    # Creates group gatherings
    SPONTANEOUS_DINER = "spontaneous"      # Last-minute decisions
    BUSY_PROFESSIONAL = "busy_professional" # Limited windows, high-end
    BUDGET_CONSCIOUS = "budget_conscious"   # Price-sensitive


class User(Base):
    """User model representing platform users."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(255))
    avatar_url = Column(String(500))

    # Location
    latitude = Column(Float)
    longitude = Column(Float)
    city = Column(String(100))

    # Simulation attributes
    is_simulated = Column(Boolean, default=False)
    persona = Column(SQLEnum(UserPersona), nullable=True)

    # Activity metrics
    activity_score = Column(Float, default=0.5)  # 0-1 scale
    social_score = Column(Float, default=0.5)    # 0-1 scale

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)

    # Relationships
    preferences = relationship("UserPreferences", back_populates="user", uselist=False)
    friendships = relationship("Friendship", foreign_keys="Friendship.user_id", back_populates="user")
    bookings = relationship("Booking", back_populates="user")
    interests = relationship("VenueInterest", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"


class UserPreferences(Base):
    """User preferences for recommendations."""
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    # Cuisine preferences (JSON array of categories)
    cuisine_preferences = Column(JSON, default=list)

    # Price range (1-4, like $-$$$$)
    min_price_level = Column(Integer, default=1)
    max_price_level = Column(Integer, default=4)

    # Ambiance preferences
    preferred_ambiance = Column(JSON, default=list)  # ["romantic", "casual", "trendy"]

    # Dietary restrictions
    dietary_restrictions = Column(JSON, default=list)  # ["vegetarian", "gluten-free"]

    # Social preferences
    preferred_group_size = Column(Integer, default=4)
    open_to_new_people = Column(Boolean, default=True)

    # Distance preference (km)
    max_distance = Column(Float, default=10.0)

    # Time preferences
    preferred_dining_times = Column(JSON, default=list)  # ["lunch", "dinner"]

    # Relationship
    user = relationship("User", back_populates="preferences")

    def __repr__(self):
        return f"<UserPreferences(user_id={self.user_id})>"


class Friendship(Base):
    """Friendship/connection between users."""
    __tablename__ = "friendships"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    friend_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Friendship metrics
    compatibility_score = Column(Float, default=0.5)  # 0-1 calculated score
    interaction_count = Column(Integer, default=0)

    # Status
    status = Column(String(20), default="active")  # active, pending, blocked

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="friendships")
    friend = relationship("User", foreign_keys=[friend_id])

    def __repr__(self):
        return f"<Friendship(user={self.user_id}, friend={self.friend_id})>"
