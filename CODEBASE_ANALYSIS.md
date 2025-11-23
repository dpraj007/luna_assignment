# Luna Social Codebase - Comprehensive Analysis

## Project Overview
Luna Social is a sophisticated FastAPI-based backend for a social dining platform featuring:
- AI-powered recommendation engine with spatial and social analysis
- LangGraph-based agents for automated bookings and simulation
- Real-time streaming with SSE and event channels
- Realistic user behavior simulation with persona-driven dynamics
- Temporal and environmental context modeling

## Technology Stack
- **Framework**: FastAPI 0.109.0
- **Database**: SQLAlchemy 2.0.25 with async SQLite (aiosqlite)
- **AI/Agents**: LangGraph 0.0.26, LangChain 0.1.4
- **Streaming**: Redis 5.0.1 (with FakeRedis for demos)
- **Async**: Python asyncio
- **Data**: Pydantic 2.5.3 for validation
- **Geospatial**: GeoPy 2.4.1 for distance calculations

---

## 1. INFERENCE LAYER (AI/ML Model Code)

### Recommendation Engine (`/backend/app/services/recommendation.py`)
**Purpose**: AI-powered venue and social compatibility scoring

**Key Features**:
- **Spatial Analysis**:
  - Haversine distance calculation for venue proximity
  - Location-based filtering within user's max_distance preference
  - Latitude/longitude coordinate matching

- **Venue Scoring Algorithm**:
  - Multi-factor scoring considering:
    - User preferences (cuisine, ambiance, price range)
    - Venue ratings and popularity
    - Distance from user location
    - Friends' activity at venues
    - Trending status
  - Method: `get_venue_recommendations(user_id, limit, filters)`

- **Social Compatibility Matching**:
  - Calculates compatibility_score between users (0-1 scale)
  - Considers:
    - Shared venue interests
    - Activity patterns
    - Social preferences (group size, openness to new people)
    - Friendship connections
  - Method: `get_compatible_users(user_id, venue_id, limit)`

- **Interest-Based Matching**:
  - Identifies users interested in same venues
  - Time slot compatibility
  - Invitation openness scoring
  - Method: `get_users_interested_in_venue()`

**Algorithms Used**:
- Haversine formula for geographic distance
- Weighted multi-criteria scoring system
- Preference evolution learning

### Preference Evolution Service (`/backend/app/services/preference_evolution.py`)
**Purpose**: Machine learning-based preference learning from user interactions

**Components**:
- Tracks user interaction history (views, saves, bookings)
- Updates preference weights based on behavior
- Social influence modeling (friends' preferences)
- Temporal pattern learning
- Cold-start user handling

---

## 2. AGENTS LAYER (Agent Implementations)

### Booking Agent (`/backend/app/agents/booking_agent.py`)
**Purpose**: Automated reservation management and group booking orchestration

**Workflow** (State-based execution):
1. **_validate_venue()**: Check venue exists, accepts reservations, has capacity
2. **_find_optimal_time()**: Select booking time based on user preferences or defaults
3. **_create_booking()**: Insert booking record with confirmation code
4. **_send_invitations()**: Send invitations to group members
5. **_confirm_booking()**: Mark booking as confirmed

**Key Methods**:
- `create_booking(user_id, venue_id, party_size, preferred_time, group_members, special_requests)`
  - Returns: booking_id, confirmation_code, status, invitations_sent
  - Publishes booking_created and booking_confirmed events

- `auto_book_interested_users(venue_id)`
  - Groups compatible users interested in same venue
  - Creates bookings automatically
  - Simple pairing algorithm for group formation

**Event Publishing**:
- `booking_created`: When booking record created
- `invite_sent`: When invitations sent to group members
- `booking_confirmed`: When booking confirmed

### Recommendation Agent (`/backend/app/agents/recommendation_agent.py`)
**Purpose**: Intelligent venue and social recommendations with explanations

**Workflow** (State-based execution):
1. **_analyze_context()**: Extract user context (time, location, meal period, persona)
2. **_get_venue_recommendations()**: Score and rank venues
3. **_get_people_recommendations()**: Find compatible users for venue
4. **_publish_recommendation_event()**: Track for analytics

**Key Methods**:
- `get_recommendations(user_id, include_people=True)`
  - Returns: venues list, people list, context, explanations
  - Context includes: meal_time, is_weekend, user_location, preferences

- `track_interaction(user_id, interaction_type, venue_id, target_user_id, metadata)`
  - Records user interactions (view, save, invite, booking)
  - Used for recommendation learning

- `express_interest(user_id, venue_id, preferred_time_slot, open_to_invites)`
  - Marks user interest in venue
  - Enables social matching
  - Returns other interested users

**Context Analysis**:
- Time-based: breakfast, lunch, afternoon, dinner, late_night
- Day-based: weekend vs weekday detection
- Location-based: User latitude/longitude
- Persona-based: User archetype (social_butterfly, foodie_explorer, etc.)

### Simulator Agent (`/backend/app/agents/simulator_agent.py`)
**Purpose**: Individual user behavior simulation for demo environments

**Simulated Actions**:
1. **_browse_venues()**: View recommendations (5-60s duration)
2. **_check_friend_activity()**: View friend profiles
3. **_express_interest()**: Save venue for later
4. **_send_invite()**: Invite friend to venue
5. **_respond_invite()**: Accept/decline invitation (70% acceptance rate)
6. **_make_booking()**: Create venue reservation

**Persona-Based Behavior Weights**:
- SOCIAL_BUTTERFLY: 1.5x check_friends, 1.5x send_invite
- FOODIE_EXPLORER: 1.3x browse, 1.3x express_interest
- EVENT_ORGANIZER: 2.0x send_invite, 1.5x make_booking
- SPONTANEOUS_DINER: 1.5x make_booking
- ROUTINE_REGULAR: 0.7x browse (consistent patterns)
- BUSY_PROFESSIONAL: 0.5x browse, 1.2x make_booking
- BUDGET_CONSCIOUS: 1.2x browse, 0.8x express_interest

### Simulation Orchestrator (`/backend/app/agents/simulator_agent.py`)
**Purpose**: Master control for simulated ecosystem behavior

**Key Features**:
- Manages active user pool (30 users default, up to 100)
- Advances simulation time with configurable speed
- Triggers predefined scenarios with behavior modifications
- Publishes metrics and events

**Scenario Modifiers**:
- **normal**: Baseline behavior
- **lunch_rush**: +1.5x browse, +2.0x make_booking
- **friday_night**: +2.0x send_invite, +1.5x check_friends
- **weekend_brunch**: +1.5x express_interest, +1.3x browse
- **concert_night**: +1.5x send_invite, +1.5x make_booking
- **new_user_onboarding**: +2.0x browse, +1.5x check_friends

**Control Methods**:
- `start(speed, scenario)`: Begin simulation
- `pause()`: Temporarily halt
- `resume()`: Continue from pause
- `stop()`: End simulation
- `reset()`: Clear all state
- `set_speed(multiplier)`: 1.0 = real-time, >1.0 = accelerated
- `trigger_scenario(scenario)`: Activate specific behavior pattern

**Metrics Tracking**:
- events_generated: Total simulation events
- bookings_created: Successful reservations
- invites_sent: Invitation count
- active_users: Current active user count

### LangGraph Simulation Orchestrator (`/backend/app/agents/simulator_graph.py`)
**Purpose**: Advanced graph-based simulation using LangGraph state architecture

**Graph Nodes** (execution pipeline):
1. **UserPoolManager**: Load and manage active users, build social graph
2. **BehaviorEngine**: Select actions for users based on weighted probabilities
3. **ActionExecutor**: Execute selected actions (browse, invite, book, etc.)
4. **StateUpdater**: Update venue states, metrics, social graph
5. **EventEmitter**: Publish aggregated events to streams

**State Type: SimulationGraphState**
- simulation_time: Current simulated time
- speed_multiplier: Time acceleration factor
- active_users: List of user IDs in simulation
- selected_actions: Dict of user_id -> action details
- executed_events: List of completed event data
- venue_states: Dict tracking venue popularity, bookings
- social_graph: Dict of user_id -> friend_id list
- metrics: Aggregated simulation metrics
- scenario, action_probabilities, persona_modifiers, temporal_modifiers

**Advanced Features**:
- Asynchronous node execution
- State persistence between ticks
- Temporal modifier integration
- Dynamic persona modifier application
- Scenario-based behavior modulation

---

## 3. FASTAPI BACKEND STRUCTURE

### Main Application (`/backend/app/main.py`)
**Entry Point**: `app = FastAPI(...)`

**Configuration**:
- Title: "Luna Social Backend"
- Version: 1.0.0
- API Prefix: `/api/v1`
- CORS: Enabled for all origins
- Lifespan: Async context manager with db initialization

**Core Middleware**:
- CORSMiddleware for frontend access
- Logging at DEBUG or INFO level

**Startup**: `init_db()` - Creates all SQLAlchemy tables
**Root Endpoint**: `GET /` - Returns API info
**Health Check**: `GET /health` - Returns {"status": "healthy"}

### Database Configuration (`/backend/app/core/database.py`)
**Database Engine**:
- URL: `sqlite+aiosqlite:///./luna_social.db` (default)
- Async SQLAlchemy with AsyncSession
- Echo enabled in DEBUG mode
- Connection pool: 5 min, 10 max overflow

**Key Functions**:
- `get_db()`: FastAPI dependency for DB sessions
- `init_db()`: Create all tables at startup
- `drop_db()`: Clear all tables
- Base: Declarative base for all models

### Settings/Configuration (`/backend/app/core/config.py`)
**Pydantic BaseSettings** with environment variable support

**Key Settings**:
- App: DEBUG, LOG_LEVEL
- Database: DATABASE_URL, pool sizes
- Redis/Streaming: REDIS_URL, STREAM_BACKEND (memory/redis/kafka)
- Simulation: DEFAULT_SIMULATION_SPEED, SIMULATION_TICK_INTERVAL_SECONDS
- Recommendations: COMPATIBILITY_THRESHOLD, MAX_DISTANCE_KM
- Feature Flags: ENABLE_WEBSOCKET, ENABLE_KAFKA, ENABLE_REPLAY
- APIs: MAPBOX_TOKEN, OPENAI_API_KEY (optional)

---

## 4. DATABASE MODELS

### User Models (`/backend/app/models/user.py`)

**User** (Table: users)
- Primary Fields: id, email, username, full_name, avatar_url
- Location: latitude, longitude, city
- Simulation: is_simulated, persona (UserPersona enum)
- Metrics: activity_score, social_score (0-1)
- Timestamps: created_at, last_active
- Relationships: preferences, friendships, bookings, interests

**UserPersona** (Enum):
- SOCIAL_BUTTERFLY: High activity, many friends
- FOODIE_EXPLORER: Tries new venues, writes reviews
- ROUTINE_REGULAR: Consistent patterns
- EVENT_ORGANIZER: Creates group gatherings
- SPONTANEOUS_DINER: Last-minute decisions
- BUSY_PROFESSIONAL: Limited windows, high-end preferences
- BUDGET_CONSCIOUS: Price-sensitive

**UserPreferences** (Table: user_preferences)
- cuisine_preferences: JSON array
- Price Range: min_price_level, max_price_level (1-4)
- Ambiance: preferred_ambiance (romantic, casual, trendy, etc.)
- Dietary: dietary_restrictions (vegetarian, gluten-free, etc.)
- Social: preferred_group_size, open_to_new_people
- Distance: max_distance (km)
- Timing: preferred_dining_times (lunch, dinner, brunch)

**Friendship** (Table: friendships)
- user_id, friend_id: User references
- compatibility_score: 0-1 calculated score
- interaction_count: Total interactions
- status: active, pending, blocked
- created_at: Timestamp

### Booking Models (`/backend/app/models/booking.py`)

**Booking** (Table: bookings)
- References: user_id, venue_id
- Details: party_size, booking_time, duration_minutes
- Status: pending, confirmed, cancelled, completed, no_show
- Group: group_members (JSON array of user IDs)
- Special: special_requests, confirmation_code
- Tracking: created_by_agent ("booking_agent", "user")
- Timestamps: created_at, updated_at

**BookingInvitation** (Table: booking_invitations)
- Relationships: booking_id, inviter_id, invitee_id
- Status: pending, accepted, declined
- Message: Custom invitation message
- responded_at: Response timestamp
- created_at: Timestamp

### Venue Models (`/backend/app/models/venue.py`)

**Venue** (Table: venues)
- Identity: id, name, description
- Location: address, city, latitude, longitude
- Category: category (restaurant, bar, cafe, club, lounge, etc.)
- Cuisine: cuisine_type (italian, japanese, mexican, etc.)
- Pricing: price_level (1-4 scale)
- Ratings: rating (0-5), review_count
- Ambiance: ambiance (JSON array: romantic, trendy, casual, etc.)
- Capacity: capacity, current_occupancy, is_available property
- Operations: accepts_reservations, operating_hours (JSON)
- Features: features (JSON array: outdoor_seating, live_music, happy_hour, etc.)
- Media: image_url, photos (JSON array)
- Popularity: popularity_score (0-1), trending (boolean)
- Timestamps: created_at, updated_at

**VenueCategory** (Constants):
- RESTAURANT, BAR, CAFE, CLUB, LOUNGE
- BRUNCH_SPOT, FINE_DINING, CASUAL_DINING, FAST_CASUAL

### Interaction Models (`/backend/app/models/interaction.py`)

**UserInteraction** (Table: user_interactions)
- user_id: Who performed action
- interaction_type: InteractionType enum
- venue_id, target_user_id: Optional references
- duration_seconds: Time spent (for views)
- metadata: JSON object with context
- created_at: Timestamp (indexed)

**InteractionType** (Enum):
- VIEW, SEARCH, SAVE, SHARE, REVIEW, LIKE
- INVITE_SENT, INVITE_RECEIVED, INVITE_ACCEPTED, INVITE_DECLINED
- FRIEND_REQUEST, PROFILE_VIEW, APP_OPEN, BROWSE

**VenueInterest** (Table: venue_interests)
- user_id, venue_id: Composite identifier
- interest_score: 0-1 float
- explicitly_interested: Boolean (1=yes, 0=no) - stored as int for SQLite
- preferred_date, preferred_time_slot: Timing preferences
- open_to_invites: Boolean (1=yes, 0=no)
- created_at, updated_at: Timestamps

### Event Models (`/backend/app/models/event.py`)

**SimulationEvent** (Table: simulation_events)
- event_type: EventType enum (indexed)
- channel: Stream channel name (indexed)
- payload: JSON event data
- user_id, venue_id, booking_id: Optional references
- simulation_time: Time in simulation (DateTime)
- created_at: Real timestamp (indexed)
- to_dict(): Converts to JSON-serializable dict

**EventType** (Enum - 20+ types):
- User: USER_CREATED, USER_ACTIVE, USER_BROWSE, USER_SEARCH, USER_INTEREST
- Social: FRIEND_REQUEST, FRIEND_ACCEPTED, INVITE_SENT, INVITE_RESPONSE
- Booking: BOOKING_CREATED, BOOKING_CONFIRMED, BOOKING_CANCELLED, BOOKING_COMPLETED
- Recommendation: RECOMMENDATION_GENERATED, COMPATIBILITY_CALCULATED
- System: SIMULATION_STARTED, SIMULATION_PAUSED, SIMULATION_RESUMED, SIMULATION_RESET, SCENARIO_TRIGGERED
- Venue: VENUE_TRENDING, VENUE_AVAILABILITY_CHANGE

---

## 5. API ENDPOINTS

### Base URL: `/api/v1`

### Users Routes (`/api/v1/users`)
- `GET /` - List users (paginated, with simulated_only filter)
- `GET /{user_id}` - Get user details
- `GET /{user_id}/preferences` - Get user preferences
- `GET /{user_id}/friends` - Get user's friend list with compatibility scores

### Venues Routes (`/api/v1/venues`)
- `GET /` - List venues (filters: category, min_rating, trending_only)
- `GET /trending` - Get trending venues sorted by popularity
- `GET /{venue_id}` - Get venue details
- `GET /{venue_id}/interested` - Get users interested in venue

### Recommendations Routes (`/api/v1/recommendations`)
- `GET /{user_id}` - Get personalized recommendations (venues + people)
- `GET /{user_id}/venues` - Get venue recommendations only
- `GET /{user_id}/people` - Get people recommendations
- `POST /{user_id}/interest` - Express interest in venue
- `GET /group/{user_ids}` - Get optimal venue for group

### Bookings Routes (`/api/v1/bookings`)
- `GET /` - List all bookings (paginated, status filter)
- `GET /{booking_id}` - Get booking details
- `POST /{user_id}/create` - Create new booking (uses BookingAgent)
- `GET /user/{user_id}` - Get user's bookings
- `POST /{booking_id}/cancel` - Cancel a booking
- `POST /venue/{venue_id}/auto-book` - Auto-book interested users

### Simulation Routes (`/api/v1/simulation`)
- `POST /start` - Start simulation (speed, scenario)
- `POST /pause` - Pause simulation
- `POST /resume` - Resume simulation
- `POST /stop` - Stop simulation
- `POST /reset` - Reset simulation state
- `POST /speed` - Set simulation speed multiplier
- `POST /scenario` - Trigger scenario (lunch_rush, friday_night, etc.)
- `GET /state` - Get current simulation state
- `GET /metrics` - Get simulation metrics
- `GET /scenarios` - List available scenarios

### Admin Routes (`/api/v1/admin`)

**Dashboard & Stats**:
- `GET /stats` - Overall dashboard statistics

**Streaming Subscriptions (SSE)**:
- `GET /streams/subscribe/{channel}` - Subscribe to single channel
- `GET /streams/subscribe-all` - Subscribe to all channels
- `GET /streams/history/{channel}` - Get historical events
- `GET /streams/channels` - List available channels

**Data Management**:
- `POST /data/seed` - Seed demo data (user_count parameter)
- `POST /data/reset` - Clear database

**Control Endpoints**:
- `POST /control/users/spawn/{count}` - Spawn simulated users
- `POST /control/events/trigger` - Trigger custom event
- `POST /control/behavior/adjust` - Adjust behavior probabilities

**Metrics**:
- `GET /metrics/streaming` - Streaming service metrics
- `GET /metrics/realtime` - Real-time metrics as SSE stream
- `GET /metrics/aggregate` - Aggregated metrics (time_range, group_by)

**Environment**:
- `GET /environment/context` - Get environment context (weather, traffic)
- `GET /environment/temporal` - Get temporal context (time, meal period)

**WebSocket**:
- `WS /control/ws` - Bidirectional control (set_speed, set_scenario, spawn_users, etc.)

---

## 6. SERVICES LAYER

### Streaming Service (`/backend/app/services/streaming.py`)
**Purpose**: Real-time event distribution via SSE and optional Redis

**Available Channels**:
- user_actions: User behavior (browsing, searches, interests)
- recommendations: Generated recommendations
- bookings: Booking activities
- social_interactions: Friend requests, invites
- system_metrics: Performance metrics
- simulation_control: Simulation events
- environmental: Weather, events

**Implementation**:
- InMemoryStreamBackend (default for demos)
- AsyncQueue-based event distribution
- Max 1000 events per stream (trimmed)
- Subscriber management per channel
- Event history tracking

**Methods**:
- `publish_event(event_type, channel, payload, simulation_time, user_id, venue_id, booking_id)`
- `subscribe(channel)` - Returns asyncio.Queue
- `unsubscribe(channel, queue)`
- `get_history(channel, limit)`
- `clear_streams()`

### Data Generator (`/backend/app/services/data_generator.py`)
**Purpose**: Seed realistic demo data

**Generated Data**:
- Users: 50-200 count, random personas, locations in NYC area
- Venues: 30 sample venues with realistic NYC coordinates
- Preferences: Randomized cuisine, ambiance, price preferences
- Friendships: Random friend connections with compatibility scores
- Venue Interests: Pre-populated user interests

**Location Bounds** (NYC Demo):
- Latitude: 40.70 to 40.78
- Longitude: -74.02 to -73.93

**Methods**:
- `seed_all(user_count)` - Generate complete dataset
- `generate_users(count)` - Create users with personas
- `generate_venues()` - Create venue records
- `generate_preferences(user_id)` - Randomize user prefs

### Temporal Event Generator (`/backend/app/services/temporal.py`)
**Purpose**: Model time-based behavioral patterns

**Time Context Analysis**:
- Hour, minute, day_of_week, day_of_month
- Meal periods: breakfast (6-11), lunch (11-15), afternoon (15-18), dinner (18-22), late_night (22-24)
- Weekend detection (Saturday-Sunday)
- Holiday detection (Valentine's, Thanksgiving, Christmas, etc.)
- Season calculation (spring, summer, fall, winter)

**Action Modifiers by Time**:
- Meal periods affect booking/browsing probability
- Weekends increase social interactions
- Holidays trigger special scenarios
- Morning hours favor cafes/brunch spots
- Evening hours favor restaurants/bars

**Methods**:
- `get_time_context(datetime)` - Return TimeContext
- `get_action_modifiers(time_context)` - Return probability adjustments
- `get_recommended_scenarios(time_context)` - Suggest scenarios

### Analytics Service (`/backend/app/services/analytics.py`)
**Purpose**: Track and analyze user behavior patterns

**Tracking**:
- User journey tracking
- Event aggregation
- Trend detection
- Metrics calculation

### Environment Service (`/backend/app/services/environment.py`)
**Purpose**: Model environmental factors affecting decisions

**Context Factors**:
- Weather (sunny, rainy, snowy)
- Traffic conditions
- Special events happening
- Seasonal factors

**Methods**:
- `get_environment_context(location, time)` - Return environment state

### Preference Evolution (`/backend/app/services/preference_evolution.py`)
**Purpose**: ML-based learning from user interactions

**Learning Mechanisms**:
- View/Save frequency tracking
- Booking success rate
- Rating correlations
- Social influence (friends' preferences)
- Temporal patterns

---

## 7. PROJECT STRUCTURE

```
/home/user/luna_assignment/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI app entry point
│   │   ├── core/
│   │   │   ├── config.py              # Settings with env support
│   │   │   └── database.py            # SQLAlchemy setup
│   │   ├── models/
│   │   │   ├── user.py                # User, UserPreferences, Friendship
│   │   │   ├── booking.py             # Booking, BookingInvitation
│   │   │   ├── venue.py               # Venue, VenueCategory
│   │   │   ├── interaction.py         # UserInteraction, VenueInterest
│   │   │   └── event.py               # SimulationEvent, EventType
│   │   ├── agents/
│   │   │   ├── booking_agent.py       # Booking automation agent
│   │   │   ├── recommendation_agent.py # Recommendation orchestrator
│   │   │   ├── simulator_agent.py     # Individual user simulator
│   │   │   └── simulator_graph.py     # LangGraph orchestrator
│   │   ├── api/
│   │   │   ├── __init__.py            # Router aggregation
│   │   │   └── routes/
│   │   │       ├── users.py           # User endpoints
│   │   │       ├── venues.py          # Venue endpoints
│   │   │       ├── recommendations.py # Recommendation endpoints
│   │   │       ├── bookings.py        # Booking endpoints
│   │   │       ├── simulation.py      # Simulation control
│   │   │       └── admin.py           # Admin/dashboard endpoints
│   │   └── services/
│   │       ├── recommendation.py      # Recommendation engine (inference)
│   │       ├── streaming.py           # Event streaming service
│   │       ├── data_generator.py      # Demo data generation
│   │       ├── temporal.py            # Time-based modifiers
│   │       ├── environment.py         # Environmental context
│   │       ├── preference_evolution.py # ML preference learning
│   │       └── analytics.py           # Behavior analysis
│   ├── requirements.txt
│   └── .env.example
├── frontend/                          # React/Vue frontend (not analyzed)
├── tests/                             # Multi-layer test suite
│   ├── conftest.py                    # Pytest configuration and fixtures
│   ├── layer1_inference/              # Inference algorithm tests
│   ├── layer2_agents/                 # Agent behavior tests
│   ├── layer3_backend/                # Backend and database tests
│   └── layer4_api/                    # API integration tests
├── README.md
├── implementation_plan.md
├── IMPLEMENTATION_GAP_ANALYSIS.md
└── final_analysis_report_01.md
```

---

## 8. RESPONSE/REQUEST MODELS (Pydantic)

### Key Response Models:
- `UserResponse`: id, username, full_name, email, city, scores
- `VenueRecommendation`: venue details + score + distance
- `PersonRecommendation`: user + compatibility + reasons
- `BookingResponse`: booking details with status
- `VenueResponse`: complete venue information

### Request Models:
- `BookingRequest`: venue_id, party_size, preferred_time, group_members
- `InterestRequest`: venue_id, preferred_time_slot, open_to_invites
- `SimulationStartRequest`: speed, scenario
- `TriggerEventRequest`: event_type, channel, payload

---

## 9. RUNNING & DEPLOYMENT

### Starting Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Database
- Location: `./luna_social.db` (SQLite in project root)
- Schema: Auto-created on startup via `init_db()`
- Async sessions: AsyncSessionLocal factory

### Required Environment Variables (see .env.example)
- DATABASE_URL (default: sqlite+aiosqlite)
- REDIS_URL (optional, uses in-memory fallback)
- OPENAI_API_KEY (optional, for LLM features)
- DEBUG (default: True)

---

## 10. KEY ARCHITECTURAL PATTERNS

### 1. **Agent Pattern** (LangChain)
- State-based execution flow
- Step-by-step workflow with error handling
- Event publication at each stage
- Database persistence

### 2. **Dependency Injection** (FastAPI)
- `Depends(get_db)` for database access
- `Depends(get_orchestrator)` for singleton
- Async context managers for resource management

### 3. **Event-Driven Architecture**
- Pub/Sub via streaming service
- Event types for all major actions
- SSE for real-time client updates
- Event history for replay capability

### 4. **Multi-Factor Scoring**
- Weighted algorithm for venue recommendations
- Haversine for distance calculation
- User preference matching
- Popularity/trending factors
- Friend activity signals

### 5. **Simulation as First-Class Feature**
- Persona-driven behavior
- Scenario-based modulation
- Time acceleration support
- Metrics tracking and publishing

