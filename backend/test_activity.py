import asyncio
import sys
import os

# Add the backend directory to the path (where this script is located)
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from app.core.database import get_db, engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User, Friendship
from app.models.booking import Booking
from app.models.venue import Venue
from datetime import datetime, timedelta

async def test_query():
    async with AsyncSession(engine) as db:
        # Get friend IDs for user 1
        friend_query = select(Friendship.friend_id).where(Friendship.user_id == 1)
        friend_result = await db.execute(friend_query)
        friend_ids = [row[0] for row in friend_result.all()]
        
        print(f"Friend IDs: {friend_ids}")
        
        if not friend_ids:
            print("No friends found")
            return
        
        # Get recent bookings from friends
        cutoff_time = datetime.utcnow() - timedelta(days=7)
        booking_query = select(
            Booking.user_id,
            Booking.venue_id,
            Booking.created_at,
            User.username,
            User.avatar_url,
            Venue.name.label('venue_name'),
            Venue.cuisine_type
        ).join(
            User, Booking.user_id == User.id
        ).join(
            Venue, Booking.venue_id == Venue.id
        ).where(
            Booking.user_id.in_(friend_ids),
            Booking.created_at >= cutoff_time,
            Booking.status.in_(['confirmed', 'pending'])
        ).order_by(Booking.created_at.desc()).limit(20)
        
        booking_result = await db.execute(booking_query)
        bookings = booking_result.all()
        
        print(f"Found {len(bookings)} bookings")
        for row in bookings:
            print(f"  - {row.username} booked {row.venue_name} at {row.created_at}")

if __name__ == "__main__":
    asyncio.run(test_query())

