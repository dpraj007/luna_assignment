# Luna Social - Quick Reference Guide

## Key File Paths (Absolute)

### Core Application
- `/home/user/luna_assignment/backend/app/main.py` - FastAPI app entry point
- `/home/user/luna_assignment/backend/app/core/config.py` - Settings/config
- `/home/user/luna_assignment/backend/app/core/database.py` - DB setup

### Inference Layer
- `/home/user/luna_assignment/backend/app/services/recommendation.py` - Recommendation engine with spatial analysis

### Agents
- `/home/user/luna_assignment/backend/app/agents/booking_agent.py` - Booking automation (5-step workflow)
- `/home/user/luna_assignment/backend/app/agents/recommendation_agent.py` - Recommendation orchestrator
- `/home/user/luna_assignment/backend/app/agents/simulator_agent.py` - User behavior simulator + SimulationOrchestrator
- `/home/user/luna_assignment/backend/app/agents/simulator_graph.py` - LangGraph-based orchestrator

### Models
- `/home/user/luna_assignment/backend/app/models/user.py` - User, UserPreferences, Friendship, UserPersona
- `/home/user/luna_assignment/backend/app/models/booking.py` - Booking, BookingInvitation
- `/home/user/luna_assignment/backend/app/models/venue.py` - Venue, VenueCategory
- `/home/user/luna_assignment/backend/app/models/interaction.py` - UserInteraction, VenueInterest, InteractionType
- `/home/user/luna_assignment/backend/app/models/event.py` - SimulationEvent, EventType

### API Routes
- `/home/user/luna_assignment/backend/app/api/__init__.py` - Router configuration
- `/home/user/luna_assignment/backend/app/api/routes/users.py` - User endpoints
- `/home/user/luna_assignment/backend/app/api/routes/venues.py` - Venue endpoints
- `/home/user/luna_assignment/backend/app/api/routes/recommendations.py` - Recommendation endpoints
- `/home/user/luna_assignment/backend/app/api/routes/bookings.py` - Booking endpoints
- `/home/user/luna_assignment/backend/app/api/routes/simulation.py` - Simulation control
- `/home/user/luna_assignment/backend/app/api/routes/admin.py` - Admin/dashboard endpoints

### Services
- `/home/user/luna_assignment/backend/app/services/recommendation.py` - Recommendation engine
- `/home/user/luna_assignment/backend/app/services/streaming.py` - Event streaming (SSE)
- `/home/user/luna_assignment/backend/app/services/data_generator.py` - Demo data seeding
- `/home/user/luna_assignment/backend/app/services/temporal.py` - Time-based modifiers
- `/home/user/luna_assignment/backend/app/services/environment.py` - Environmental context
- `/home/user/luna_assignment/backend/app/services/preference_evolution.py` - ML preference learning
- `/home/user/luna_assignment/backend/app/services/analytics.py` - Behavior analysis

### Documentation
- `/home/user/luna_assignment/CODEBASE_ANALYSIS.md` - Comprehensive analysis (this file)
- `/home/user/luna_assignment/IMPLEMENTATION_GAP_ANALYSIS.md` - Gap analysis
- `/home/user/luna_assignment/final_analysis_report_01.md` - Final report

---

## Critical Components Summary

### 1. Inference Layer
**File**: `recommendation.py`
- Multi-factor venue scoring (preferences, distance, popularity, friends' activity)
- Haversine distance calculation
- Social compatibility matching
- Interest-based user grouping

### 2. Agents
**Files**: 4 agent files
- **BookingAgent**: Validate venue → find time → create booking → send invites → confirm
- **RecommendationAgent**: Analyze context → recommend venues → recommend people → publish event
- **SimulatorAgent**: Individual user actions (browse, invite, book, etc.)
- **SimulationOrchestrator**: Master control (start, pause, stop, scenario triggers)
- **LangGraphOrchestrator**: Advanced graph-based orchestration with 5 nodes

### 3. Database Models
**File**: 5 model files
- **Users**: User, UserPreferences, Friendship (with 7 personas)
- **Bookings**: Booking, BookingInvitation (with 5 statuses)
- **Venues**: Venue (with categories: restaurant, bar, cafe, club, lounge, etc.)
- **Interactions**: UserInteraction, VenueInterest (with 13 interaction types)
- **Events**: SimulationEvent, EventType (with 20+ event types)

### 4. API Endpoints
**6 route files**: 40+ endpoints across 6 major routes
- Users (4 endpoints)
- Venues (4 endpoints)
- Recommendations (5 endpoints)
- Bookings (6 endpoints)
- Simulation (8 endpoints)
- Admin (15+ endpoints including SSE, WebSocket, metrics)

### 5. Services
**7 service files**
- Recommendation engine (spatial + social)
- Streaming (event pub/sub)
- Data generation (seeding)
- Temporal modifiers (time-based)
- Environment modeling
- Preference evolution (ML)
- Analytics

---

## Key Algorithms

### Venue Recommendation Scoring
```
score = (preference_match * 0.4) + 
        (popularity * 0.3) + 
        (rating * 0.2) + 
        (friend_activity * 0.1)
- Filtered by: distance, price range, cuisine, ambiance
```

### User Compatibility Calculation
```
compatibility = (shared_interests * 0.4) +
                (activity_similarity * 0.3) +
                (social_preference_match * 0.3)
```

### Persona-Based Action Weights
```
Base probabilities:
- browse: 0.40
- check_friends: 0.20
- express_interest: 0.15
- send_invite: 0.10
- respond_invite: 0.10
- make_booking: 0.05

Applied modifiers: persona (1.5x-2.0x), scenario (1.3x-2.0x), temporal (context-based)
```

---

## Simulation Features

### Scenarios
1. **normal** - Baseline behavior
2. **lunch_rush** - High booking, increased browsing (11:30 AM - 1:30 PM)
3. **friday_night** - Social interactions, group formation
4. **weekend_brunch** - Leisure browsing, larger groups
5. **concert_night** - Event-driven dining
6. **new_user_onboarding** - Cold start learning

### Event Types (20+)
- User: CREATE, ACTIVE, BROWSE, SEARCH, INTEREST
- Social: FRIEND_REQUEST, FRIEND_ACCEPTED, INVITE_SENT/RESPONSE
- Booking: CREATED, CONFIRMED, CANCELLED, COMPLETED
- Recommendation: GENERATED, COMPATIBILITY_CALCULATED
- System: SIMULATION_STARTED/PAUSED/RESUMED/RESET
- Venue: TRENDING, AVAILABILITY_CHANGE

---

## Testing Capabilities

### Unit Testing
```
pytest /home/user/luna_assignment/tests/
```

### Manual Testing
1. Seed demo data: `POST /api/v1/admin/data/seed?user_count=50`
2. Start simulation: `POST /api/v1/simulation/start` (speed=1.0, scenario=normal)
3. Watch stream: `GET /api/v1/admin/streams/subscribe/user_actions`
4. Get recommendations: `GET /api/v1/recommendations/{user_id}`
5. Create booking: `POST /api/v1/bookings/{user_id}/create`

### Load Testing
- Up to 100 active simulated users
- Configurable speed multiplier (1.0 = real-time, 10+ = accelerated)
- Metrics streaming via SSE

---

## Critical Configuration Points

### Database
- Default: SQLite (luna_social.db)
- Can be changed to PostgreSQL via DATABASE_URL env var
- Async sessions for concurrency

### Streaming
- Default: In-memory backend (AsyncQueue-based)
- Alternative: Redis for distributed systems
- 1000 events per stream max (auto-trimmed)

### Simulation
- Default speed: 1.0 (real-time)
- Default active users: 30 (max 100)
- Tick interval: 1 second

### API
- Prefix: /api/v1
- CORS: All origins (configure for production)
- Debug: True (disable in production)

---

## Performance Characteristics

### Recommendation Engine
- Venue scoring: O(n) where n = total venues
- People matching: O(m) where m = active users
- Distance calculation: Haversine (O(1) per pair)

### Simulation
- Supports 30+ active users simultaneously
- Can accelerate time up to 100x
- Event publishing via asyncio queues

### Database
- Async SQLAlchemy for non-blocking I/O
- Connection pooling (5 min, 10 max)
- Indexes on: event_type, channel, created_at, user_id, venue_id

