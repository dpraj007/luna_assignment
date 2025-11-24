"""
Script to populate friend activity data for the user-app feed.
"""
import asyncio
import sys
import random
from datetime import datetime, timedelta

sys.path.insert(0, '/home/ubuntu/ETC/Luna_assignemnt/luna_assignment/backend')

from app.core.database import get_db, engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User, Friendship
from app.models.venue import Venue
from app.models.booking import Booking, BookingStatus
from app.models.interaction import UserInteraction, VenueInterest, InteractionType

async def populate_friend_activity():
    async with AsyncSession(engine) as db:
        # Get user 1
        user1_query = select(User).where(User.id == 1)
        result = await db.execute(user1_query)
        user1 = result.scalar_one()
        print(f"User 1: {user1.username}")
        
        # Get some other users to be friends
        other_users_query = select(User).where(User.id != 1, User.is_simulated == True).limit(10)
        result = await db.execute(other_users_query)
        other_users = result.scalars().all()
        print(f"Found {len(other_users)} potential friends")
        
        if len(other_users) < 5:
            print("Not enough users! Please seed data first.")
            return
        
        # Create friendships for user 1
        friends = other_users[:5]
        for friend in friends:
            friendship = Friendship(
                user_id=1,
                friend_id=friend.id,
                compatibility_score=random.uniform(0.6, 0.95),
                interaction_count=random.randint(5, 50),
                status="accepted",
                created_at=datetime.utcnow() - timedelta(days=random.randint(30, 180))
            )
            db.add(friendship)
            print(f"  Created friendship with {friend.username}")
        
        await db.commit()
        print(f"\n✅ Created {len(friends)} friendships for user 1")
        
        # Get some venues
        venues_query = select(Venue).limit(20)
        result = await db.execute(venues_query)
        venues = result.scalars().all()
        print(f"\nFound {len(venues)} venues")
        
        if len(venues) < 5:
            print("Not enough venues! Please seed data first.")
            return
        
        # Create recent activity for friends
        activity_count = 0
        
        for friend in friends:
            # Create 1-3 recent bookings
            num_bookings = random.randint(1, 3)
            for _ in range(num_bookings):
                venue = random.choice(venues)
                booking_time = datetime.utcnow() + timedelta(days=random.randint(1, 14))
                created_time = datetime.utcnow() - timedelta(hours=random.randint(1, 48))
                
                booking = Booking(
                    user_id=friend.id,
                    venue_id=venue.id,
                    party_size=random.randint(2, 6),
                    booking_time=booking_time,
                    status=random.choice([BookingStatus.CONFIRMED, BookingStatus.PENDING]),
                    confirmation_code=f"LUN{random.randint(10000, 99999)}",
                    created_at=created_time,
                    updated_at=created_time
                )
                db.add(booking)
                activity_count += 1
                print(f"  {friend.username} booked {venue.name}")
            
            # Create 1-2 venue interests
            num_interests = random.randint(1, 2)
            for _ in range(num_interests):
                venue = random.choice(venues)
                created_time = datetime.utcnow() - timedelta(hours=random.randint(1, 72))
                
                interest = VenueInterest(
                    user_id=friend.id,
                    venue_id=venue.id,
                    interest_score=random.uniform(0.7, 1.0),
                    explicitly_interested=1,
                    open_to_invites=1,
                    created_at=created_time,
                    updated_at=created_time
                )
                db.add(interest)
                activity_count += 1
                print(f"  {friend.username} is interested in {venue.name}")
            
            # Create 0-2 reviews
            num_reviews = random.randint(0, 2)
            for _ in range(num_reviews):
                venue = random.choice(venues)
                created_time = datetime.utcnow() - timedelta(hours=random.randint(1, 96))
                
                review = UserInteraction(
                    user_id=friend.id,
                    venue_id=venue.id,
                    interaction_type=InteractionType.REVIEW,
                    created_at=created_time
                )
                db.add(review)
                activity_count += 1
                print(f"  {friend.username} reviewed {venue.name}")
        
        await db.commit()
        print(f"\n✅ Created {activity_count} activity items for friends")
        print("\n🎉 Friend activity data populated successfully!")

if __name__ == "__main__":
    asyncio.run(populate_friend_activity())
