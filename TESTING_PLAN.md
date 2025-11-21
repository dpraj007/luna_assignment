# Luna Social - Multi-Layer Testing Plan

## Overview

This document outlines a comprehensive 4-layer testing strategy for the Luna Social platform, covering inference algorithms, agent behaviors, backend services, and full API integration.

---

## Testing Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    LAYER 4: FULL API TESTING                    │
│         End-to-end integration tests, load testing              │
├─────────────────────────────────────────────────────────────────┤
│                LAYER 3: FASTAPI BACKEND & DATABASE              │
│    Route handlers, services, models, database operations        │
├─────────────────────────────────────────────────────────────────┤
│                    LAYER 2: AGENTS TESTING                      │
│   Booking Agent, Recommendation Agent, Simulator Agent          │
├─────────────────────────────────────────────────────────────────┤
│                   LAYER 1: INFERENCE TESTING                    │
│   Recommendation Engine, Scoring Algorithms, ML Components      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Layer 1: Inference Testing

### Purpose
Test the core recommendation and scoring algorithms that power the platform's intelligence.

### Components to Test

#### 1.1 Venue Scoring Algorithm (`recommendation.py`)
- **Haversine Distance Calculation**
  - Test accuracy of distance calculations
  - Edge cases: same location, antipodal points, equator crossing

- **Preference Matching**
  - Cuisine type matching
  - Price range scoring
  - Ambiance preference alignment
  - Group size compatibility

- **Popularity & Rating Scoring**
  - Rating weight calculations
  - Popularity normalization
  - Recency bias in trending venues

#### 1.2 Social Compatibility Matching
- **Interest Overlap Scoring**
  - Shared venue interests
  - Similar activity patterns
  - Complementary preferences

- **Friendship Scoring**
  - Friend-of-friend connections
  - Interaction frequency weights
  - Compatibility score normalization

#### 1.3 Group Recommendation Engine
- **Interest-Based Grouping**
  - Optimal group size calculations
  - Venue capacity constraints
  - Time slot preference alignment

### Test Files
```
tests/
├── layer1_inference/
│   ├── __init__.py
│   ├── test_venue_scoring.py
│   ├── test_distance_calculation.py
│   ├── test_preference_matching.py
│   ├── test_social_compatibility.py
│   └── test_group_recommendations.py
```

### Key Test Cases
| Test Case | Input | Expected Output |
|-----------|-------|-----------------|
| Distance: Same location | (40.7, -74.0), (40.7, -74.0) | 0.0 km |
| Distance: NYC to Brooklyn | (40.758, -73.985), (40.678, -73.944) | ~9.5 km |
| Preference: Perfect match | User likes Italian, Venue is Italian | Score = 1.0 |
| Preference: Price mismatch | User: budget, Venue: expensive | Score < 0.5 |
| Compatibility: High overlap | 80% shared interests | Score > 0.8 |

---

## Layer 2: Agents Testing

### Purpose
Validate agent state machines, workflows, and autonomous behaviors.

### Components to Test

#### 2.1 Booking Agent (`booking_agent.py`)
- **State Machine Transitions**
  - validate_venue → find_time → create_booking → send_invites → confirm
  - Error states and recovery

- **Venue Validation**
  - Capacity checking
  - Availability verification
  - Reservation conflict detection

- **Time Slot Selection**
  - Meal period optimization
  - User preference alignment
  - Availability constraints

- **Event Publishing**
  - `booking_created` event format
  - `invite_sent` notifications
  - `booking_confirmed` completion

#### 2.2 Recommendation Agent (`recommendation_agent.py`)
- **Context Analysis**
  - Time-of-day awareness
  - Location-based filtering
  - Meal period detection
  - Persona consideration

- **Recommendation Generation**
  - Venue scoring integration
  - Result ranking
  - Diversity in recommendations

- **People Matching**
  - Compatible user identification
  - Mutual interest detection

#### 2.3 Simulator Agent (`simulator_agent.py`)
- **Action Selection**
  - Persona-based behavior weights
  - Random action distribution
  - Action duration compliance

- **Behavior Simulation**
  - Browse venue (5-60s duration)
  - Check friend activity
  - Express interest
  - Send/respond to invitations
  - Make bookings

- **Persona Behaviors**
  | Persona | Browse | Friends | Invites | Booking |
  |---------|--------|---------|---------|---------|
  | SOCIAL_BUTTERFLY | 1.0x | 1.5x | 1.5x | 1.0x |
  | FOODIE_EXPLORER | 1.3x | 0.8x | 0.8x | 1.2x |
  | EVENT_ORGANIZER | 0.8x | 1.2x | 2.0x | 1.0x |
  | BUSY_PROFESSIONAL | 0.5x | 0.7x | 1.0x | 1.2x |

#### 2.4 Simulation Orchestrator
- **Speed Control**
  - Real-time (1.0x) execution
  - Accelerated (100x+) simulation
  - Pause/resume functionality

- **Scenario Execution**
  - Normal weekday
  - Lunch rush
  - Friday night
  - Weekend brunch
  - Happy hour

- **Metrics Collection**
  - Event counting
  - Booking tracking
  - Invite statistics

### Test Files
```
tests/
├── layer2_agents/
│   ├── __init__.py
│   ├── test_booking_agent.py
│   ├── test_recommendation_agent.py
│   ├── test_simulator_agent.py
│   ├── test_orchestrator.py
│   └── test_agent_events.py
```

---

## Layer 3: FastAPI Backend & Database Testing

### Purpose
Test API route handlers, services, and database operations.

### Components to Test

#### 3.1 Database Models
- **User Models**
  - User creation and validation
  - UserPreferences CRUD
  - Friendship relationships
  - Persona assignments

- **Venue Models**
  - Venue creation with all fields
  - JSON field handling (features, tags)
  - Location indexing

- **Booking Models**
  - Booking lifecycle
  - Invitation states
  - Status transitions

- **Interaction Models**
  - Event logging
  - Interest tracking
  - Activity history

#### 3.2 Database Operations
- **Connection Management**
  - Async session handling
  - Connection pooling
  - Transaction rollback

- **CRUD Operations**
  - Create with validation
  - Read with relationships
  - Update partial fields
  - Soft delete handling

- **Query Performance**
  - Index utilization
  - Eager loading
  - Pagination efficiency

#### 3.3 Services
- **Recommendation Service**
  - Database integration
  - Cache behavior
  - Error handling

- **Streaming Service**
  - Event publishing
  - Subscription management
  - Redis fallback

- **Data Generator**
  - Seed data consistency
  - Unique constraint handling
  - Relationship integrity

### Test Files
```
tests/
├── layer3_backend/
│   ├── __init__.py
│   ├── test_models/
│   │   ├── test_user_model.py
│   │   ├── test_venue_model.py
│   │   ├── test_booking_model.py
│   │   └── test_interaction_model.py
│   ├── test_database/
│   │   ├── test_connection.py
│   │   ├── test_transactions.py
│   │   └── test_queries.py
│   └── test_services/
│       ├── test_recommendation_service.py
│       ├── test_streaming_service.py
│       └── test_data_generator.py
```

---

## Layer 4: Full API Integration Testing

### Purpose
End-to-end testing of all API endpoints with real HTTP requests.

### Components to Test

#### 4.1 User Endpoints (`/api/v1/users`)
| Method | Endpoint | Test Cases |
|--------|----------|------------|
| GET | `/users` | List all users, pagination, filtering |
| GET | `/users/{id}` | Valid ID, invalid ID, not found |
| GET | `/users/{id}/preferences` | Preferences exist, default values |
| GET | `/users/{id}/friends` | Friends list, empty list |
| PUT | `/users/{id}/preferences` | Update preferences, validation |

#### 4.2 Venue Endpoints (`/api/v1/venues`)
| Method | Endpoint | Test Cases |
|--------|----------|------------|
| GET | `/venues` | List venues, filter by cuisine |
| GET | `/venues/trending` | Trending calculation, empty DB |
| GET | `/venues/{id}` | Valid venue, not found |
| GET | `/venues/{id}/interested` | Users interested in venue |

#### 4.3 Recommendation Endpoints (`/api/v1/recommendations`)
| Method | Endpoint | Test Cases |
|--------|----------|------------|
| GET | `/recommendations` | Personalized results |
| POST | `/recommendations/interest` | Express interest |
| GET | `/recommendations/group` | Group recommendations |

#### 4.4 Booking Endpoints (`/api/v1/bookings`)
| Method | Endpoint | Test Cases |
|--------|----------|------------|
| POST | `/bookings` | Create booking, validation |
| GET | `/bookings` | List user bookings |
| GET | `/bookings/{id}` | Booking details |
| DELETE | `/bookings/{id}` | Cancel booking |
| POST | `/bookings/auto-book` | Auto-book interested users |

#### 4.5 Simulation Endpoints (`/api/v1/simulation`)
| Method | Endpoint | Test Cases |
|--------|----------|------------|
| POST | `/simulation/start` | Start simulation |
| POST | `/simulation/pause` | Pause running simulation |
| POST | `/simulation/resume` | Resume paused simulation |
| POST | `/simulation/stop` | Stop simulation |
| GET | `/simulation/state` | Get current state |
| GET | `/simulation/metrics` | Get metrics |
| POST | `/simulation/speed` | Change speed |

#### 4.6 Admin Endpoints (`/api/v1/admin`)
| Method | Endpoint | Test Cases |
|--------|----------|------------|
| GET | `/admin/dashboard` | Dashboard stats |
| GET | `/admin/streams/subscribe/{channel}` | SSE streaming |
| POST | `/admin/data/seed` | Seed data |
| POST | `/admin/data/reset` | Reset database |
| POST | `/admin/spawn-users` | Create test users |

### Integration Test Scenarios

#### Scenario 1: User Journey
```
1. Create user → Set preferences → Get recommendations
2. Express interest in venue → Find compatible people
3. Create booking → Send invites → Confirm booking
```

#### Scenario 2: Simulation Flow
```
1. Seed database → Start simulation → Monitor events
2. Adjust speed → Trigger scenario → Collect metrics
3. Pause → Resume → Stop simulation
```

#### Scenario 3: Real-time Streaming
```
1. Subscribe to SSE channel → Trigger actions
2. Verify events received → Check event format
3. Unsubscribe → Verify cleanup
```

### Test Files
```
tests/
├── layer4_api/
│   ├── __init__.py
│   ├── test_user_endpoints.py
│   ├── test_venue_endpoints.py
│   ├── test_recommendation_endpoints.py
│   ├── test_booking_endpoints.py
│   ├── test_simulation_endpoints.py
│   ├── test_admin_endpoints.py
│   ├── test_integration_scenarios.py
│   └── test_load_performance.py
```

---

## Test Configuration

### pytest.ini
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
addopts = -v --tb=short --strict-markers
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow running tests
    layer1: Inference layer tests
    layer2: Agent layer tests
    layer3: Backend layer tests
    layer4: API layer tests
```

### Test Database Strategy
- **SQLite in-memory** for unit tests
- **SQLite file** for integration tests
- **Automatic cleanup** after each test
- **Fixtures** for common test data

---

## Coverage Requirements

| Layer | Minimum Coverage | Target Coverage |
|-------|-----------------|-----------------|
| Layer 1: Inference | 90% | 95% |
| Layer 2: Agents | 85% | 90% |
| Layer 3: Backend | 80% | 90% |
| Layer 4: API | 75% | 85% |
| **Overall** | **82%** | **90%** |

---

## Test Execution Commands

```bash
# Run all tests
pytest

# Run specific layer
pytest tests/layer1_inference/ -v
pytest tests/layer2_agents/ -v
pytest tests/layer3_backend/ -v
pytest tests/layer4_api/ -v

# Run with coverage
pytest --cov=backend/app --cov-report=html

# Run by marker
pytest -m "layer1 and not slow"
pytest -m "integration"

# Run specific test file
pytest tests/layer2_agents/test_booking_agent.py -v

# Run with parallel execution
pytest -n auto
```

---

## CI/CD Integration

```yaml
# .github/workflows/tests.yml
name: Multi-Layer Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt
          pip install pytest-asyncio pytest-cov pytest-xdist

      - name: Run Layer 1 Tests
        run: pytest tests/layer1_inference/ -v --cov

      - name: Run Layer 2 Tests
        run: pytest tests/layer2_agents/ -v --cov

      - name: Run Layer 3 Tests
        run: pytest tests/layer3_backend/ -v --cov

      - name: Run Layer 4 Tests
        run: pytest tests/layer4_api/ -v --cov

      - name: Upload Coverage
        uses: codecov/codecov-action@v3
```

---

## Test Data Fixtures

### Sample Users
```python
TEST_USERS = [
    {"username": "alice", "persona": "SOCIAL_BUTTERFLY"},
    {"username": "bob", "persona": "FOODIE_EXPLORER"},
    {"username": "charlie", "persona": "EVENT_ORGANIZER"},
    {"username": "diana", "persona": "BUSY_PROFESSIONAL"},
]
```

### Sample Venues
```python
TEST_VENUES = [
    {"name": "Italian Bistro", "cuisine": "italian", "price": "$$"},
    {"name": "Sushi Palace", "cuisine": "japanese", "price": "$$$"},
    {"name": "Taco Stand", "cuisine": "mexican", "price": "$"},
]
```

---

## Summary

This 4-layer testing strategy ensures:
1. **Algorithmic correctness** through inference testing
2. **Behavioral accuracy** through agent testing
3. **Data integrity** through backend testing
4. **System reliability** through API testing

Total estimated test cases: **150+** across all layers.
