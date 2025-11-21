"""
Venue models for Luna Social.
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from ..core.database import Base


class VenueCategory(str):
    """Venue category constants."""
    RESTAURANT = "restaurant"
    BAR = "bar"
    CAFE = "cafe"
    CLUB = "club"
    LOUNGE = "lounge"
    BRUNCH_SPOT = "brunch_spot"
    FINE_DINING = "fine_dining"
    CASUAL_DINING = "casual_dining"
    FAST_CASUAL = "fast_casual"


class Venue(Base):
    """Venue model representing restaurants, bars, etc."""
    __tablename__ = "venues"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Location
    address = Column(String(500))
    city = Column(String(100), index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    # Category and type
    category = Column(String(50), index=True)  # restaurant, bar, cafe, etc.
    cuisine_type = Column(String(100))  # italian, japanese, american, etc.

    # Pricing (1-4 scale, like $-$$$$)
    price_level = Column(Integer, default=2)

    # Ratings
    rating = Column(Float, default=4.0)
    review_count = Column(Integer, default=0)

    # Ambiance tags
    ambiance = Column(JSON, default=list)  # ["romantic", "trendy", "casual"]

    # Capacity and availability
    capacity = Column(Integer, default=50)
    current_occupancy = Column(Integer, default=0)
    accepts_reservations = Column(Boolean, default=True)

    # Operating hours (JSON with day: {open, close})
    operating_hours = Column(JSON, default=dict)

    # Features
    features = Column(JSON, default=list)  # ["outdoor_seating", "live_music", "happy_hour"]

    # Media
    image_url = Column(String(500))
    photos = Column(JSON, default=list)

    # Popularity metrics
    popularity_score = Column(Float, default=0.5)  # 0-1 scale
    trending = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    bookings = relationship("Booking", back_populates="venue")
    interests = relationship("VenueInterest", back_populates="venue")

    def __repr__(self):
        return f"<Venue(id={self.id}, name={self.name})>"

    @property
    def is_available(self) -> bool:
        """Check if venue has availability."""
        return self.current_occupancy < self.capacity
