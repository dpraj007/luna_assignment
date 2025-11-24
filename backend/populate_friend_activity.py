"""
Script to populate friend activity data for the user-app feed.
"""
import asyncio
import sys
import os
import random
from datetime import datetime, timedelta

# Add the backend directory to the path (where this script is located)
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

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
        other_user_ids = [u.id for u in other_users]  # Store IDs before any commits
        print(f"Found {len(other_users)} potential friends")
        
        if len(other_users) < 5:
            print("Not enough users! Please seed data first.")
            return
        
        # Create friendships for user 1
        friends = other_users[:5]
        friend_ids = [f.id for f in friends]  # Store IDs before any commits
        friend_usernames = {f.id: f.username for f in friends}  # Store usernames before any commits
        created_count = 0
        for friend in friends:
            # Check if friendship already exists
            existing_query = select(Friendship).where(
                Friendship.user_id == 1,
                Friendship.friend_id == friend.id
            )
            result = await db.execute(existing_query)
            existing = result.first()
            
            if existing:
                print(f"  Friendship with {friend.username} already exists, skipping")
                continue
            
            friendship = Friendship(
                user_id=1,
                friend_id=friend.id,
                compatibility_score=random.uniform(0.6, 0.95),
                interaction_count=random.randint(5, 50),
                status="accepted",
                created_at=datetime.utcnow() - timedelta(days=random.randint(30, 180))
            )
            db.add(friendship)
            created_count += 1
            print(f"  Created friendship with {friend.username}")
        
        await db.commit()
        print(f"\n✅ Created {created_count} new friendships for user 1")
        
        # Get some venues
        venues_query = select(Venue).limit(20)
        result = await db.execute(venues_query)
        venues = result.scalars().all()
        print(f"\nFound {len(venues)} venues")
        
        if len(venues) < 5:
            print("Not enough venues! Please seed data first.")
            return
        
        # Review texts to use for generating reviews
        review_texts = [
            'Amazing food and great atmosphere!',
            'Loved this place, will definitely come back!',
            'Great experience, highly recommended!',
            'Fantastic service and delicious meals!',
            'One of my favorite spots in the city!',
            'Perfect for a date night!',
            'The ambiance was incredible!',
            'Best restaurant I\'ve tried this month!',
            'Great value for money!',
            'Will be recommending to all my friends!',
            'Good food but service was slow.',
            'Nice place, decent prices.',
            'Had a great time here!',
            'The food was okay, nothing special.',
            'Beautiful decor and friendly staff!'
        ]
        
        # Store venue IDs and names before any commits
        venue_ids = [v.id for v in venues]
        venue_names = {v.id: v.name for v in venues}
        
        # Create recent activity for friends
        activity_count = 0
        
        for friend_id in friend_ids:
            username = friend_usernames[friend_id]
            # Create 1-3 recent bookings
            num_bookings = random.randint(1, 3)
            for _ in range(num_bookings):
                venue_id = random.choice(venue_ids)
                venue_name = venue_names[venue_id]
                booking_time = datetime.utcnow() + timedelta(days=random.randint(1, 14))
                created_time = datetime.utcnow() - timedelta(hours=random.randint(1, 48))
                
                booking = Booking(
                    user_id=friend_id,
                    venue_id=venue_id,
                    party_size=random.randint(2, 6),
                    booking_time=booking_time,
                    status=random.choice([BookingStatus.CONFIRMED, BookingStatus.PENDING]),
                    confirmation_code=f"LUN{random.randint(10000, 99999)}",
                    created_at=created_time,
                    updated_at=created_time
                )
                db.add(booking)
                activity_count += 1
                print(f"  {username} booked {venue_name}")
            
            # Create 1-2 venue interests
            num_interests = random.randint(1, 2)
            for _ in range(num_interests):
                venue_id = random.choice(venue_ids)
                venue_name = venue_names[venue_id]
                created_time = datetime.utcnow() - timedelta(hours=random.randint(1, 72))
                
                interest = VenueInterest(
                    user_id=friend_id,
                    venue_id=venue_id,
                    interest_score=random.uniform(0.7, 1.0),
                    explicitly_interested=1,
                    open_to_invites=1,
                    created_at=created_time,
                    updated_at=created_time
                )
                db.add(interest)
                activity_count += 1
                print(f"  {username} is interested in {venue_name}")
            
            # Create 0-2 reviews with metadata
            num_reviews = random.randint(0, 2)
            for _ in range(num_reviews):
                venue_id = random.choice(venue_ids)
                venue_name = venue_names[venue_id]
                created_time = datetime.utcnow() - timedelta(hours=random.randint(1, 96))
                rating = round(random.uniform(3.5, 5.0), 1)
                
                review = UserInteraction(
                    user_id=friend_id,
                    venue_id=venue_id,
                    interaction_type=InteractionType.REVIEW,
                    interaction_metadata={
                        'rating': rating,
                        'review_text': random.choice(review_texts)
                    },
                    created_at=created_time
                )
                db.add(review)
                activity_count += 1
                print(f"  {username} reviewed {venue_name} ({rating}/5.0)")
        
        await db.commit()
        print(f"\n✅ Created {activity_count} activity items for friends")
        
        # Also create some reviews from non-friends to populate the "All Reviews" view
        print("\n📝 Creating reviews from other users...")
        # Use stored IDs instead of accessing objects after commit
        non_friend_user_ids = [uid for uid in other_user_ids if uid not in friend_ids][:10]
        
        review_count = 0
        for user_id in non_friend_user_ids:
            num_reviews = random.randint(1, 3)
            for _ in range(num_reviews):
                venue_id = random.choice(venue_ids)
                created_time = datetime.utcnow() - timedelta(hours=random.randint(1, 168))  # Up to 7 days ago
                
                review = UserInteraction(
                    user_id=user_id,
                    venue_id=venue_id,
                    interaction_type=InteractionType.REVIEW,
                    interaction_metadata={
                        'rating': round(random.uniform(3.0, 5.0), 1),
                        'review_text': random.choice(review_texts)
                    },
                    created_at=created_time
                )
                db.add(review)
                review_count += 1
        
        await db.commit()
        print(f"✅ Created {review_count} reviews from other users")
        print(f"\n🎉 Friend activity data populated successfully!")
        print(f"   Total activity items: {activity_count + review_count}")

if __name__ == "__main__":
    asyncio.run(populate_friend_activity())

