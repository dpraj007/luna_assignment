# Luna Social Backend API Documentation

This document provides a comprehensive overview of the API endpoints available in the Luna Social Backend.

## Base URL

All API endpoints are prefixed with `/api/v1`.

## Authentication

(Add authentication details if applicable, currently open based on code review)

---

## Users

### List Users
`GET /users/`

List all users with optional filtering.

**Parameters:**
- `skip` (query, int, default=0): Number of records to skip.
- `limit` (query, int, default=20): Number of records to return (max 100).
- `simulated_only` (query, bool, default=False): Filter for simulated users only.

**Response:** List of `UserResponse` objects.

### Get User
`GET /users/{user_id}`

Get detailed information for a specific user.

**Parameters:**
- `user_id` (path, int): The ID of the user.

**Response:** `UserResponse` object.

### Get User Preferences
`GET /users/{user_id}/preferences`

Get dining and social preferences for a user.

**Parameters:**
- `user_id` (path, int): The ID of the user.

**Response:** `UserPreferencesResponse` object.

### Get User Friends
`GET /users/{user_id}/friends`

Get a list of friends for a user.

**Parameters:**
- `user_id` (path, int): The ID of the user.
- `limit` (query, int, default=20): Max number of friends to return.

**Response:** List of `FriendResponse` objects.

---

## Venues

### List Venues
`GET /venues/`

List all venues with optional filters.

**Parameters:**
- `skip` (query, int, default=0): Number of records to skip.
- `limit` (query, int, default=20): Number of records to return.
- `category` (query, str, optional): Filter by venue category.
- `min_rating` (query, float, optional): Filter by minimum rating.
- `trending_only` (query, bool, default=False): Filter for trending venues only.

**Response:** List of `VenueResponse` objects.

### Get Trending Venues
`GET /venues/trending`

Get a list of currently trending venues.

**Parameters:**
- `limit` (query, int, default=10): Number of venues to return.

**Response:** List of `VenueResponse` objects.

### Get Venue
`GET /venues/{venue_id}`

Get detailed information for a specific venue.

**Parameters:**
- `venue_id` (path, int): The ID of the venue.

**Response:** `VenueResponse` object.

### Get Interested Users
`GET /venues/{venue_id}/interested`

Get users who have expressed interest in a specific venue.

**Parameters:**
- `venue_id` (path, int): The ID of the venue.
- `limit` (query, int, default=20): Max number of users to return.

**Response:** List of `InterestedUserResponse` objects.

---

## Recommendations

### Get Recommendations
`GET /recommendations`

Get personalized recommendations for a user (venues and people).

**Parameters:**
- `user_id` (query, int): The ID of the user.
- `include_people` (query, bool, default=True): Whether to include people recommendations.

**Response:** `RecommendationResponse` object.

### Get User Recommendations (Path)
`GET /recommendations/user/{user_id}`

Alternative endpoint to get recommendations using path parameter.

**Parameters:**
- `user_id` (path, int): The ID of the user.
- `include_people` (query, bool, default=True): Whether to include people recommendations.

**Response:** `RecommendationResponse` object.

### Get Venue Recommendations
`GET /recommendations/{user_id}/venues`

Get only venue recommendations for a user.

**Parameters:**
- `user_id` (path, int): The ID of the user.
- `limit` (query, int, default=10): Number of venues to return.
- `category` (query, str, optional): Filter by category.

**Response:** Object containing list of venues.

### Get Compatible People
`GET /recommendations/compatible`

Get people recommendations based on compatibility.

**Parameters:**
- `user_id` (query, int): The ID of the user.
- `venue_id` (query, int, optional): Contextual venue ID.
- `limit` (query, int, default=10): Number of people to return.

**Response:** Object containing list of people.

### Express Interest
`POST /recommendations/interest`

Express interest in a venue, potentially triggering social matching.

**Body:** `InterestRequest`
- `user_id`: int
- `venue_id`: int
- `preferred_time_slot`: str (optional)
- `open_to_invites`: bool

**Response:** `InterestResponse` object.

### Get Group Recommendations
`GET /recommendations/group`

Get optimal venue recommendations for a group of users.

**Parameters:**
- `user_ids` (query, str): Comma-separated list of user IDs.

**Response:** Object containing optimal venues and group size.

---

## Bookings

### List Bookings
`GET /bookings/`

List all bookings.

**Parameters:**
- `skip` (query, int, default=0): Number of records to skip.
- `limit` (query, int, default=20): Number of records to return.
- `status` (query, str, optional): Filter by booking status.

**Response:** List of `BookingResponse` objects.

### Get Booking
`GET /bookings/{booking_id}`

Get details of a specific booking.

**Parameters:**
- `booking_id` (path, int): The ID of the booking.

**Response:** `BookingResponse` object.

### Create Booking
`POST /bookings/{user_id}/create`

Create a new booking using the AI booking agent.

**Parameters:**
- `user_id` (path, int): The ID of the user creating the booking.

**Body:** `BookingRequest`
- `venue_id`: int
- `party_size`: int
- `preferred_time`: datetime (optional)
- `group_members`: List[int] (optional)
- `special_requests`: str (optional)

**Response:** `CreateBookingResponse` object.

### Get User Bookings
`GET /bookings/user/{user_id}`

Get all bookings for a specific user.

**Parameters:**
- `user_id` (path, int): The ID of the user.
- `status` (query, str, optional): Filter by status.

**Response:** List of `BookingResponse` objects.

### Cancel Booking
`POST /bookings/{booking_id}/cancel`

Cancel an existing booking.

**Parameters:**
- `booking_id` (path, int): The ID of the booking.

**Response:** Success status and booking ID.

### Auto-Book Venue
`POST /bookings/venue/{venue_id}/auto-book`

Trigger the booking agent to automatically match and book interested users for a venue.

**Parameters:**
- `venue_id` (path, int): The ID of the venue.

**Response:** Details of created bookings.

---

## Simulation

### Start Simulation
`POST /simulation/start`

Start the user behavior simulation.

**Body:** `SimulationStartRequest`
- `speed`: float (default=1.0)
- `scenario`: str (default="normal")

### Pause Simulation
`POST /simulation/pause`

Pause the running simulation.

### Resume Simulation
`POST /simulation/resume`

Resume a paused simulation.

### Stop Simulation
`POST /simulation/stop`

Stop the simulation completely.

### Reset Simulation
`POST /simulation/reset`

Reset the simulation state.

### Set Speed
`POST /simulation/speed`

Adjust the simulation speed multiplier.

**Body:** `SimulationSpeedRequest`
- `speed`: float

### Trigger Scenario
`POST /simulation/scenario`

Trigger a specific simulation scenario (e.g., "lunch_rush", "friday_night").

**Body:** `ScenarioRequest`
- `scenario`: str

### Get State
`GET /simulation/state`

Get the current state of the simulation (running, paused, etc.).

### Get Metrics
`GET /simulation/metrics`

Get current simulation metrics. @terminal:bash @terminal:bash @terminal:bash 

### List Scenarios
`GET /simulation/scenarios`

List all available simulation scenarios with descriptions.

---

## Admin & Dashboard

### Dashboard Stats
`GET /admin/stats`

Get high-level statistics for the admin dashboard (users, venues, bookings).

### Subscribe to Stream
`GET /admin/streams/subscribe/{channel}`

Subscribe to a Server-Sent Events (SSE) stream for real-time updates.

**Parameters:**
- `channel` (path, str): The channel to subscribe to (e.g., "user_actions", "bookings").
- `include_history` (query, bool, default=False): Whether to include recent history.

### Subscribe to All Streams
`GET /admin/streams/subscribe-all`

Subscribe to all available SSE channels.

### Get Stream History
`GET /admin/streams/history/{channel}`

Get historical events for a specific channel.

### List Channels
`GET /admin/streams/channels`

List all available event stream channels.

### Seed Data
`POST /admin/data/seed`

Seed the database with demo data.

**Parameters:**
- `user_count` (query, int, default=50): Number of users to generate.

### Reset Data
`POST /admin/data/reset`

**WARNING:** Clears the entire database and re-initializes it.

### Streaming Metrics
`GET /admin/metrics/streaming`

Get metrics about the streaming service itself.

### Spawn Users
`POST /admin/control/users/spawn/{count}`

Spawn a specific number of new simulated users.

**Parameters:**
- `count` (path, int): Number of users to spawn.

### Trigger Event
`POST /admin/control/events/trigger`

Manually trigger a custom simulation event.

**Body:** `TriggerEventRequest`

### Adjust Behavior
`POST /admin/control/behavior/adjust`

Adjust global or persona-specific simulation behavior probabilities.

**Body:** `AdjustBehaviorRequest`

### Realtime Metrics
`GET /admin/metrics/realtime`

Stream system metrics in real-time via SSE.

### Aggregate Metrics
`GET /admin/metrics/aggregate`

Get aggregated metrics over a specified time range.

**Parameters:**
- `time_range` (query, str): "1h", "24h", "7d", "30d"
- `group_by` (query, str): "minute", "hour", "day"

### Environment Context
`GET /admin/environment/context`

Get current simulated environment details (weather, traffic).

### Temporal Context
`GET /admin/environment/temporal`

Get current simulated time context (time of day, meal period).

### WebSocket Control
`WS /admin/control/ws`

Bidirectional WebSocket connection for real-time admin control.

### LLM Status
`GET /admin/llm/status`

Get the configuration status of the LLM integration (OpenRouter).

### Test LLM
`POST /admin/llm/test`

Test the LLM connection with a simple prompt.
