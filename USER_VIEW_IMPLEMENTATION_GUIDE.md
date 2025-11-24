# User View Implementation Guide

## Quick Start Guide for Customer-Facing Application

### Overview

This guide provides step-by-step instructions for implementing the User View - the customer-facing application that showcases how Luna Social's AI-powered recommendations and social dining features work for end users.

---

## Project Setup

### 1. Initialize Next.js Application

```bash
# In the luna_assignment directory
npx create-next-app@latest user-app --typescript --tailwind --app
cd user-app

# Install additional dependencies
npm install @radix-ui/react-avatar @radix-ui/react-dialog @radix-ui/react-dropdown-menu
npm install @radix-ui/react-tabs @radix-ui/react-toast
npm install framer-motion zustand socket.io-client
npm install mapbox-gl @mapbox/mapbox-gl-geocoder
npm install recharts lucide-react
npm install next-pwa
```

### 2. Project Structure

```
user-app/
├── app/
│   ├── layout.tsx                 # Root layout with providers
│   ├── page.tsx                   # Home/Dashboard
│   ├── discover/
│   │   └── page.tsx              # Venue discovery
│   ├── venues/
│   │   └── [id]/
│   │       └── page.tsx          # Venue detail
│   ├── bookings/
│   │   ├── page.tsx              # My bookings
│   │   └── new/
│   │       └── page.tsx          # New booking flow
│   ├── social/
│   │   ├── page.tsx              # Social features
│   │   └── groups/
│   │       └── [id]/
│   │           └── page.tsx      # Group management
│   ├── profile/
│   │   └── page.tsx              # User profile & stats
│   └── api/
│       └── [...].ts              # API routes if needed
├── components/
│   ├── user/
│   │   ├── UserHeader.tsx        # Profile header
│   │   ├── ForYouFeed.tsx        # Recommendations
│   │   ├── SocialActivity.tsx    # Friends activity
│   │   └── QuickActions.tsx      # Action buttons
│   ├── venue/
│   │   ├── VenueCard.tsx         # Venue display card
│   │   ├── VenueMap.tsx          # Map integration
│   │   ├── VenueFilters.tsx      # Smart filters
│   │   └── VenueDetail.tsx       # Detail view
│   ├── booking/
│   │   ├── BookingWizard.tsx     # Booking flow
│   │   ├── GroupFormation.tsx    # Group coordination
│   │   ├── BookingCard.tsx       # Booking display
│   │   └── TimeSlots.tsx         # Availability grid
│   ├── social/
│   │   ├── FriendsList.tsx       # Friends management
│   │   ├── DiningPartners.tsx    # Partner matching
│   │   ├── GroupCard.tsx         # Group display
│   │   └── Invitations.tsx       # Invite management
│   └── shared/
│       ├── Notification.tsx      # Notification system
│       ├── LoadingStates.tsx     # Skeletons
│       └── ErrorBoundary.tsx     # Error handling
├── hooks/
│   ├── useRecommendations.ts     # Recommendation logic
│   ├── useBooking.ts             # Booking management
│   ├── useSocialFeatures.ts      # Social interactions
│   └── useRealtimeUpdates.ts     # WebSocket/SSE
├── lib/
│   ├── api-client.ts             # API communication
│   ├── socket.ts                 # Socket.io setup
│   └── utils.ts                  # Helper functions
├── stores/
│   ├── userStore.ts              # User state (Zustand)
│   ├── venueStore.ts             # Venue state
│   └── bookingStore.ts           # Booking state
└── styles/
    └── globals.css                # Global styles
```

---

## Core Components Implementation

### 1. User Dashboard (`app/page.tsx`)

```tsx
// Example structure for the home page
import { UserHeader } from '@/components/user/UserHeader'
import { ForYouFeed } from '@/components/user/ForYouFeed'
import { SocialActivity } from '@/components/user/SocialActivity'
import { QuickActions } from '@/components/user/QuickActions'

export default function Dashboard() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-orange-50">
      <UserHeader />
      <main className="container mx-auto px-4 py-6 space-y-6">
        <ForYouFeed />
        <QuickActions />
        <SocialActivity />
      </main>
    </div>
  )
}
```

### 2. For You Feed Component

```tsx
// components/user/ForYouFeed.tsx
export function ForYouFeed() {
  // Fetch personalized recommendations
  const { recommendations, loading } = useRecommendations()

  return (
    <section className="space-y-4">
      <h2 className="text-2xl font-bold">For You</h2>
      
      {/* Hero Recommendation */}
      <div className="relative rounded-2xl overflow-hidden shadow-xl">
        {/* Large venue card with AI explanation */}
      </div>

      {/* Secondary Recommendations */}
      <div className="flex gap-4 overflow-x-auto pb-4">
        {/* Horizontal scroll of venue cards */}
      </div>
    </section>
  )
}
```

### 3. Real-time Updates Hook

```tsx
// hooks/useRealtimeUpdates.ts
import { useEffect } from 'react'
import { socket } from '@/lib/socket'
import { useUserStore } from '@/stores/userStore'

export function useRealtimeUpdates() {
  const updateNotification = useUserStore(state => state.addNotification)

  useEffect(() => {
    // Connect to WebSocket
    socket.connect()

    // Listen for events
    socket.on('recommendation:new', (data) => {
      // Handle new recommendation
    })

    socket.on('booking:update', (data) => {
      // Handle booking update
    })

    socket.on('social:invite', (data) => {
      // Handle social invitation
    })

    return () => {
      socket.disconnect()
    }
  }, [])
}
```

---

## Key Features to Implement

### Priority 1: Core User Experience
1. **User Authentication/Profile**
   - Mock login for demo
   - User persona selection
   - Basic profile display

2. **Personalized Recommendations**
   - "For You" feed with AI explanations
   - Real-time updates via SSE/WebSocket
   - Save/like functionality

3. **Venue Discovery**
   - Search with natural language
   - Filter by preferences
   - Real-time availability display

4. **Basic Booking**
   - Select venue → Pick time → Confirm
   - Show booking confirmation
   - View upcoming bookings

### Priority 2: Social Features
1. **Friend Activity Feed**
   - Show friend bookings/reviews
   - Join group options

2. **Group Booking**
   - Create group
   - Invite friends
   - Coordinate timing

3. **Dining Partner Matching**
   - Show compatible users
   - Compatibility scores
   - Send invitations

### Priority 3: Enhanced Experience
1. **Interactive Map**
   - Venue locations
   - User location
   - Friend locations (optional)

2. **User Stats Dashboard**
   - Dining patterns
   - Taste profile
   - Social metrics

3. **Reviews & Ratings**
   - Post-dining prompts
   - Photo uploads
   - Social sharing

4. **Push Notifications**
   - Real-time alerts
   - Smart suggestions
   - Social updates

---

## API Integration

### Connect to Backend

```typescript
// lib/api-client.ts
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

export const api = {
  // User endpoints
  getMe: () => fetch(`${API_BASE}/users/me`).then(r => r.json()),
  getRecommendations: (userId: number) => 
    fetch(`${API_BASE}/recommendations/user/${userId}`).then(r => r.json()),
  
  // Venue endpoints
  searchVenues: (query: string, filters: any) =>
    fetch(`${API_BASE}/venues/search?q=${query}`, {
      method: 'POST',
      body: JSON.stringify(filters)
    }).then(r => r.json()),
  
  // Booking endpoints
  createBooking: (data: BookingData) =>
    fetch(`${API_BASE}/bookings`, {
      method: 'POST',
      body: JSON.stringify(data)
    }).then(r => r.json()),
  
  // Social endpoints
  getFriendActivity: () =>
    fetch(`${API_BASE}/social/friends/activity`).then(r => r.json()),
    
  createGroup: (data: GroupData) =>
    fetch(`${API_BASE}/social/groups`, {
      method: 'POST',
      body: JSON.stringify(data)
    }).then(r => r.json()),
}
```

### Real-time Connection

```typescript
// lib/socket.ts
import { io } from 'socket.io-client'

export const socket = io(process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000', {
  autoConnect: false,
  transports: ['websocket'],
})

// Or use Server-Sent Events
export function subscribeToSSE(channel: string, onMessage: (data: any) => void) {
  const eventSource = new EventSource(
    `${process.env.NEXT_PUBLIC_API_URL}/admin/streams/subscribe/${channel}`
  )
  
  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data)
    onMessage(data)
  }
  
  return () => eventSource.close()
}
```

---

## Demo Scenarios

### Scenario 1: First-Time User
1. User opens app → Onboarding flow
2. Select preferences (cuisine, price, distance)
3. Choose persona (Foodie, Social Butterfly, etc.)
4. See personalized recommendations immediately
5. Browse and save venues
6. Make first booking

### Scenario 2: Social Dining
1. User wants to organize group dinner
2. Creates group → Selects venue
3. AI suggests compatible friends
4. Sends invitations
5. Friends respond in real-time
6. Group confirmation and chat

### Scenario 3: Quick Lunch
1. 11:45 AM - User gets notification
2. Opens app → "Lunch Near You"
3. Sees real-time availability
4. One-tap booking
5. Gets walking directions
6. Checks in at venue

---

## Styling Guide

### Color Palette
```css
/* styles/globals.css */
:root {
  --primary: #7C3AED;        /* Purple */
  --primary-dark: #5B21B6;
  --accent: #FB923C;         /* Orange */
  --success: #10B981;
  --warning: #F59E0B;
  --error: #EF4444;
  --gray-50: #F9FAFB;
  --gray-900: #111827;
}
```

### Component Styling Example
```tsx
// Venue card with Tailwind
<div className="group relative bg-white rounded-xl shadow-sm hover:shadow-xl transition-all duration-300 overflow-hidden">
  <div className="aspect-w-16 aspect-h-9 relative">
    <img src={venue.image} className="object-cover" />
    {venue.trending && (
      <div className="absolute top-2 right-2 bg-orange-500 text-white px-2 py-1 rounded-full text-xs font-bold">
        🔥 Trending
      </div>
    )}
  </div>
  <div className="p-4">
    <h3 className="font-semibold text-lg">{venue.name}</h3>
    <p className="text-gray-600 text-sm">{venue.cuisine} • {venue.distance}km</p>
    <div className="mt-2 flex items-center justify-between">
      <span className="text-sm font-medium">{venue.price}</span>
      <div className="flex items-center gap-1 text-purple-600">
        <span className="text-sm font-bold">{venue.matchScore}%</span>
        <span className="text-xs">match</span>
      </div>
    </div>
  </div>
</div>
```

---

## Testing Checklist

### Functionality
- [ ] User can see personalized recommendations
- [ ] Search and filters work correctly
- [ ] Booking flow completes successfully
- [ ] Social features (invites, groups) function
- [ ] Real-time updates appear instantly
- [ ] Notifications display properly

### User Experience
- [ ] Loading states for all async operations
- [ ] Error handling with user-friendly messages
- [ ] Smooth animations and transitions
- [ ] Mobile responsive design
- [ ] Keyboard navigation support
- [ ] Fast page loads (<3s)

### Integration
- [ ] Connects to backend API
- [ ] WebSocket/SSE updates work
- [ ] Handles offline states gracefully
- [ ] Persists user preferences
- [ ] Syncs with backend state

---

## Deployment

### Development
```bash
npm run dev
# App runs on http://localhost:3001 (to avoid conflict with admin dashboard)
```

### Production Build
```bash
npm run build
npm run start
```

### Environment Variables
```env
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_URL=ws://localhost:8000
NEXT_PUBLIC_MAPBOX_TOKEN=your_mapbox_token
```

---

## Next Steps

1. **Start with Core Components**
   - User dashboard
   - Recommendation feed
   - Basic venue browsing

2. **Add Booking Flow**
   - Venue selection
   - Time picker
   - Confirmation

3. **Implement Social Features**
   - Friend activity
   - Group creation
   - Invitations

4. **Enhance with Real-time**
   - WebSocket connection
   - Live notifications
   - Activity updates

5. **Polish for Demo**
   - Smooth animations
   - Loading states
   - Error handling
   - Demo data seeding

---

## Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [Tailwind CSS](https://tailwindcss.com)
- [Framer Motion](https://www.framer.com/motion/)
- [Zustand State Management](https://github.com/pmndrs/zustand)
- [Socket.io Client](https://socket.io/docs/v4/client-api/)
- [Mapbox GL JS](https://docs.mapbox.com/mapbox-gl-js/)

---

**Ready to Build!** 🚀

This User View will complete your Luna Social demo, showing how all the intelligent backend systems translate into a delightful user experience. The combination of Admin Dashboard, Agent Views, and User View provides a complete picture of the platform's capabilities.
