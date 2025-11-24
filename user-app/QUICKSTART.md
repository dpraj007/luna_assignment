# User View Quick Start Guide

## Installation & Setup

```bash
# Navigate to user-app directory
cd user-app

# Install dependencies
npm install

# Start development server
npm run dev
```

The app will be available at `http://localhost:3001`

## Prerequisites

1. **Backend API must be running** on `http://localhost:8000`
   ```bash
   cd ../backend
   uvicorn app.main:app --reload --port 8000
   ```

2. **Seed demo data** (if not already done)
   - Visit `http://localhost:8000/docs` and call `/api/v1/admin/data/seed`

## Features Implemented

### ✅ Core Features
- **User Dashboard** (`/`)
  - Personalized "For You" feed with AI explanations
  - Hero recommendation card
  - Secondary recommendations grid
  - Social activity feed
  - Quick actions bar

- **Venue Discovery** (`/discover`)
  - Search functionality
  - Venue grid with filters
  - Trending indicators
  - Real-time availability

- **My Bookings** (`/bookings`)
  - Upcoming bookings list
  - Past bookings history
  - Booking status tracking
  - Confirmation codes

- **Social** (`/social`)
  - Placeholder for social features

### ✅ Components
- UserHeader with persona badges
- ForYouFeed with AI reasoning
- SocialActivity feed
- QuickActions with time-based CTAs
- Navigation bar (bottom)
- Booking cards

### ✅ Integration
- API client with error handling
- Real-time updates via SSE
- Zustand state management
- Responsive design

## Demo User

The app uses **User ID 1** by default. Make sure this user exists in your database.

To change the user:
1. Edit `app/page.tsx` and `app/bookings/page.tsx`
2. Change `DEFAULT_USER_ID` constant

## Environment Variables

Create `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

## Troubleshooting

### "Failed to load user data"
- Ensure backend is running
- Check that user ID 1 exists
- Verify API URL in `.env.local`

### "No recommendations"
- Seed demo data
- Start simulation to generate activity
- Check backend logs for errors

### Styling issues
- Run `npm install` to ensure all dependencies are installed
- Clear `.next` cache: `rm -rf .next`

## Next Steps

To extend the User View:

1. **Add Booking Flow**
   - Create `/app/bookings/new/page.tsx`
   - Implement time slot selection
   - Add confirmation flow

2. **Enhance Social Features**
   - Implement group creation
   - Add friend matching
   - Create invitation system

3. **Add Venue Detail Page**
   - Create `/app/venues/[id]/page.tsx`
   - Show full venue information
   - Add booking CTA

4. **Implement Reviews**
   - Add review submission
   - Display venue reviews
   - Show friend reviews prominently

## Architecture Notes

- **State Management**: Zustand for global state
- **API**: Centralized API client in `lib/api-client.ts`
- **Real-time**: Server-Sent Events for live updates
- **Styling**: Tailwind CSS with custom design system
- **Animations**: Framer Motion for smooth transitions

## Demo Scenarios

1. **View Personalized Feed**
   - Open app → See recommendations
   - Click on venue cards
   - View AI explanations

2. **Discover Venues**
   - Navigate to Discover
   - Search for cuisines
   - Filter by preferences

3. **Check Bookings**
   - View upcoming bookings
   - See confirmation codes
   - Track booking status

## Support

For issues or questions, refer to:
- `USER_VIEW_IMPLEMENTATION_GUIDE.md` - Detailed implementation guide
- `implementation_plan.md` - Full system design
- Backend API docs at `http://localhost:8000/docs`

