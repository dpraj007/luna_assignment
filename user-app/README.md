# Luna Social - User View Application

Customer-facing application showcasing Luna Social's AI-powered dining recommendations and social features.

## Features

- **Personalized Feed**: AI-powered "For You" recommendations with explanations
- **Venue Discovery**: Smart search and filtering
- **Social Dining**: Find compatible partners, coordinate groups
- **Smart Booking**: One-tap booking with intelligent defaults
- **Real-time Updates**: Live recommendations and notifications

## Tech Stack

- **Next.js 14** with App Router
- **TypeScript** for type safety
- **Tailwind CSS** for styling
- **Framer Motion** for animations
- **Zustand** for state management
- **Server-Sent Events** for real-time updates

## Setup

### Prerequisites

- Node.js 18+
- Backend API running on `http://localhost:8000`

### Installation

```bash
cd user-app
npm install
```

### Development

```bash
npm run dev
```

The app will run on `http://localhost:3001` (to avoid conflict with admin dashboard on port 3000).

### Environment Variables

Create `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

## Project Structure

```
user-app/
├── app/
│   ├── page.tsx              # Home/Dashboard
│   ├── layout.tsx            # Root layout
│   └── globals.css           # Global styles
├── components/
│   └── user/                 # User-facing components
├── hooks/                    # Custom React hooks
├── lib/                      # Utilities and API client
└── stores/                   # Zustand state stores
```

## Demo User

By default, the app uses user ID `1`. To change this, modify `DEFAULT_USER_ID` in `app/page.tsx` or implement proper authentication.

## Features Implemented

- ✅ User Dashboard with personalized feed
- ✅ Recommendation display with AI explanations
- ✅ Social activity feed
- ✅ Quick actions bar
- ✅ Real-time updates via SSE
- ✅ Responsive design

## Coming Soon

- Venue discovery page
- Booking flow
- Group coordination
- User profile & stats
- Reviews & ratings

## License

Part of Luna Social platform demonstration.

