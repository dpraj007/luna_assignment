"""
Data generator for seeding realistic demo data.
"""
import random
from typing import List, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.user import User, UserPreferences, Friendship, UserPersona
from ..models.venue import Venue
from ..models.interaction import VenueInterest


class DataGenerator:
    """Generate realistic demo data for Luna Social."""

    # Sample data pools
    FIRST_NAMES = [
        "Emma", "Liam", "Olivia", "Noah", "Ava", "Ethan", "Sophia", "Mason",
        "Isabella", "William", "Mia", "James", "Charlotte", "Benjamin", "Amelia",
        "Lucas", "Harper", "Henry", "Evelyn", "Alexander", "Luna", "Michael",
        "Ella", "Daniel", "Elizabeth", "Matthew", "Sofia", "Aiden", "Avery",
        "Joseph", "Scarlett", "Jackson", "Grace", "Sebastian", "Chloe", "David",
        "Victoria", "Carter", "Riley", "Wyatt", "Aria", "John", "Lily", "Owen",
        "Zoey", "Dylan", "Penelope", "Luke", "Layla", "Gabriel"
    ]

    LAST_NAMES = [
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
        "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
        "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
        "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark",
        "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King",
        "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores", "Green",
        "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell"
    ]

    CUISINES = [
        "italian", "japanese", "mexican", "chinese", "indian", "thai",
        "french", "american", "mediterranean", "korean", "vietnamese",
        "greek", "spanish", "middle_eastern", "brazilian", "caribbean"
    ]

    AMBIANCE_TYPES = [
        "romantic", "casual", "trendy", "upscale", "family_friendly",
        "lively", "intimate", "outdoor", "rooftop", "waterfront"
    ]

    VENUE_FEATURES = [
        "outdoor_seating", "live_music", "happy_hour", "private_rooms",
        "pet_friendly", "vegan_options", "wine_bar", "craft_cocktails",
        "late_night", "brunch"
    ]

    # NYC-area coordinates for demo
    NYC_BOUNDS = {
        "lat_min": 40.70,
        "lat_max": 40.78,
        "lon_min": -74.02,
        "lon_max": -73.93
    }

    VENUE_NAMES = [
        ("The Golden Fork", "restaurant", "italian"),
        ("Sakura Garden", "restaurant", "japanese"),
        ("Casa Mexicana", "restaurant", "mexican"),
        ("Dragon Palace", "restaurant", "chinese"),
        ("Spice Route", "restaurant", "indian"),
        ("Thai Orchid", "restaurant", "thai"),
        ("Le Petit Bistro", "restaurant", "french"),
        ("The American Grill", "restaurant", "american"),
        ("Mediterranean Blue", "restaurant", "mediterranean"),
        ("Seoul Kitchen", "restaurant", "korean"),
        ("Pho Paradise", "restaurant", "vietnamese"),
        ("Olive & Vine", "restaurant", "greek"),
        ("Tapas & Wine", "restaurant", "spanish"),
        ("The Speakeasy", "bar", "american"),
        ("Cocktail Club", "bar", "american"),
        ("The Rooftop", "lounge", "american"),
        ("Jazz & Blues Bar", "bar", "american"),
        ("Wine Cellar", "bar", "french"),
        ("Craft Beer House", "bar", "american"),
        ("The Brunch Spot", "cafe", "american"),
        ("Morning Glory Cafe", "cafe", "american"),
        ("Espresso Lab", "cafe", "italian"),
        ("The Tea House", "cafe", "chinese"),
        ("Sunset Lounge", "lounge", "american"),
        ("Night Owl Club", "club", "american"),
        ("Fine & Dine", "fine_dining", "french"),
        ("Chef's Table", "fine_dining", "american"),
        ("Ocean View", "fine_dining", "mediterranean"),
        ("The Steakhouse", "restaurant", "american"),
        ("Vegan Vibes", "restaurant", "american"),
    ]

    def __init__(self, db: AsyncSession):
        self.db = db

    def _random_location(self) -> Tuple[float, float]:
        """Generate random location within NYC bounds."""
        lat = random.uniform(self.NYC_BOUNDS["lat_min"], self.NYC_BOUNDS["lat_max"])
        lon = random.uniform(self.NYC_BOUNDS["lon_min"], self.NYC_BOUNDS["lon_max"])
        return lat, lon

    def _random_persona(self) -> UserPersona:
        """Get random user persona."""
        return random.choice(list(UserPersona))

    async def generate_users(self, count: int = 50) -> List[User]:
        """Generate simulated users."""
        users = []

        for i in range(count):
            first_name = random.choice(self.FIRST_NAMES)
            last_name = random.choice(self.LAST_NAMES)
            username = f"{first_name.lower()}{last_name.lower()}{random.randint(1, 999)}"
            lat, lon = self._random_location()

            user = User(
                email=f"{username}@example.com",
                username=username,
                full_name=f"{first_name} {last_name}",
                avatar_url=f"https://api.dicebear.com/7.x/avataaars/svg?seed={username}",
                latitude=lat,
                longitude=lon,
                city="New York",
                is_simulated=True,
                persona=self._random_persona(),
                activity_score=random.uniform(0.3, 1.0),
                social_score=random.uniform(0.3, 1.0),
                last_active=datetime.utcnow() - timedelta(hours=random.randint(0, 48))
            )
            self.db.add(user)
            users.append(user)

        await self.db.commit()

        # Refresh to get IDs
        for user in users:
            await self.db.refresh(user)

        return users

    async def generate_user_preferences(self, users: List[User]) -> List[UserPreferences]:
        """Generate preferences for users."""
        preferences = []

        for user in users:
            # Select random cuisines (2-5)
            num_cuisines = random.randint(2, 5)
            cuisines = random.sample(self.CUISINES, num_cuisines)

            # Select random ambiance preferences (1-3)
            num_ambiance = random.randint(1, 3)
            ambiance = random.sample(self.AMBIANCE_TYPES, num_ambiance)

            # Price range based on persona
            if user.persona == UserPersona.BUDGET_CONSCIOUS:
                min_price, max_price = 1, 2
            elif user.persona == UserPersona.BUSY_PROFESSIONAL:
                min_price, max_price = 2, 4
            else:
                min_price = random.randint(1, 2)
                max_price = random.randint(min_price + 1, 4)

            pref = UserPreferences(
                user_id=user.id,
                cuisine_preferences=cuisines,
                min_price_level=min_price,
                max_price_level=max_price,
                preferred_ambiance=ambiance,
                dietary_restrictions=random.choice([[], ["vegetarian"], ["gluten-free"], []]),
                preferred_group_size=random.randint(2, 6),
                open_to_new_people=random.random() > 0.3,
                max_distance=random.uniform(5, 20),
                preferred_dining_times=random.sample(["breakfast", "lunch", "dinner", "brunch"], random.randint(1, 3))
            )
            self.db.add(pref)
            preferences.append(pref)

        await self.db.commit()
        return preferences

    async def generate_friendships(self, users: List[User], connections_per_user: int = 5) -> List[Friendship]:
        """Generate friendship connections between users."""
        friendships = []
        user_ids = [u.id for u in users]

        for user in users:
            # Get random friends (excluding self)
            possible_friends = [uid for uid in user_ids if uid != user.id]
            num_friends = min(connections_per_user, len(possible_friends))
            friend_ids = random.sample(possible_friends, num_friends)

            for friend_id in friend_ids:
                # Check if friendship already exists
                existing = any(
                    f.user_id == user.id and f.friend_id == friend_id
                    for f in friendships
                )
                if not existing:
                    friendship = Friendship(
                        user_id=user.id,
                        friend_id=friend_id,
                        compatibility_score=random.uniform(0.5, 1.0),
                        interaction_count=random.randint(0, 50),
                        status="active"
                    )
                    self.db.add(friendship)
                    friendships.append(friendship)

        await self.db.commit()
        return friendships

    async def generate_venues(self) -> List[Venue]:
        """Generate venue data."""
        venues = []

        for name, category, cuisine in self.VENUE_NAMES:
            lat, lon = self._random_location()

            # Random features (2-4)
            num_features = random.randint(2, 4)
            features = random.sample(self.VENUE_FEATURES, num_features)

            # Random ambiance (2-3)
            num_ambiance = random.randint(2, 3)
            ambiance = random.sample(self.AMBIANCE_TYPES, num_ambiance)

            # Price level based on category
            if category == "fine_dining":
                price_level = random.randint(3, 4)
            elif category in ["bar", "lounge", "club"]:
                price_level = random.randint(2, 3)
            elif category == "cafe":
                price_level = random.randint(1, 2)
            else:
                price_level = random.randint(1, 4)

            venue = Venue(
                name=name,
                description=f"A wonderful {category} serving {cuisine} cuisine in the heart of NYC.",
                address=f"{random.randint(1, 999)} {random.choice(['Main', 'Park', 'Broadway', '5th', 'Madison'])} Street",
                city="New York",
                latitude=lat,
                longitude=lon,
                category=category,
                cuisine_type=cuisine,
                price_level=price_level,
                rating=round(random.uniform(3.5, 5.0), 1),
                review_count=random.randint(10, 500),
                ambiance=ambiance,
                capacity=random.randint(20, 150),
                current_occupancy=0,
                accepts_reservations=True,
                operating_hours={
                    "monday": {"open": "11:00", "close": "23:00"},
                    "tuesday": {"open": "11:00", "close": "23:00"},
                    "wednesday": {"open": "11:00", "close": "23:00"},
                    "thursday": {"open": "11:00", "close": "23:00"},
                    "friday": {"open": "11:00", "close": "00:00"},
                    "saturday": {"open": "10:00", "close": "00:00"},
                    "sunday": {"open": "10:00", "close": "22:00"},
                },
                features=features,
                image_url=f"https://source.unsplash.com/400x300/?{category},{cuisine}",
                popularity_score=random.uniform(0.3, 1.0),
                trending=random.random() > 0.8
            )
            self.db.add(venue)
            venues.append(venue)

        await self.db.commit()

        for venue in venues:
            await self.db.refresh(venue)

        return venues

    async def generate_venue_interests(
        self,
        users: List[User],
        venues: List[Venue],
        interests_per_user: int = 3
    ) -> List[VenueInterest]:
        """Generate venue interests for users."""
        interests = []

        for user in users:
            # Random venues user is interested in
            num_interests = random.randint(1, interests_per_user)
            interested_venues = random.sample(venues, min(num_interests, len(venues)))

            for venue in interested_venues:
                interest = VenueInterest(
                    user_id=user.id,
                    venue_id=venue.id,
                    interest_score=random.uniform(0.5, 1.0),
                    explicitly_interested=random.random() > 0.5,
                    preferred_time_slot=random.choice(["breakfast", "lunch", "dinner", "brunch"]),
                    open_to_invites=random.random() > 0.3
                )
                self.db.add(interest)
                interests.append(interest)

        await self.db.commit()
        return interests

    async def seed_all(self, user_count: int = 50) -> dict:
        """Seed all demo data."""
        print(f"Generating {user_count} users...")
        users = await self.generate_users(user_count)

        print("Generating user preferences...")
        await self.generate_user_preferences(users)

        print("Generating friendships...")
        friendships = await self.generate_friendships(users)

        print("Generating venues...")
        venues = await self.generate_venues()

        print("Generating venue interests...")
        interests = await self.generate_venue_interests(users, venues)

        return {
            "users": len(users),
            "venues": len(venues),
            "friendships": len(friendships),
            "interests": len(interests)
        }
