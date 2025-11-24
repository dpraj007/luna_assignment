# How to Access the User View

## Quick Access Guide

### Prerequisites ✅

1. **Backend API must be running** on port 8000
2. **Demo data must be seeded** in the database
3. **Node.js 18+** installed

---

## Step-by-Step Setup

### 1️⃣ Start the Backend API (if not already running)

```bash
# Open Terminal 1
cd /home/ubuntu/ETC/Luna_assignemnt/luna_assignment/backend

# Activate virtual environment
source venv/bin/activate

# Start the backend
uvicorn app.main:app --reload --port 8000
```

**Verify**: Visit `http://localhost:8000/docs` - you should see the API documentation

---

### 2️⃣ Seed Demo Data (if not already done)

Option A - Via API Docs:
1. Go to `http://localhost:8000/docs`
2. Find `/api/v1/admin/data/seed` endpoint
3. Click "Try it out" → "Execute"

Option B - Via curl:
```bash
curl -X POST http://localhost:8000/api/v1/admin/data/seed
```

**This creates:**
- 20-50 simulated users (including User ID 1)
- 30-50 venues
- Friendships and preferences
- Initial bookings

---

### 3️⃣ Install User View Dependencies

```bash
# Open Terminal 2
cd /home/ubuntu/ETC/Luna_assignemnt/luna_assignment/user-app

# Install dependencies
npm install
```

**Expected output:**
```
added XXX packages in XXs
```

---

### 4️⃣ Start the User View Application

```bash
# In the user-app directory
npm run dev
```

**Expected output:**
```
▲ Next.js 14.x.x
- Local:        http://localhost:3001
✓ Ready in X.Xs
```

---

### 5️⃣ Access the User View

Open your browser and visit:

**🎯 http://localhost:3001**

You should see:
- User dashboard with persona badge
- Personalized "For You" recommendations
- Social activity feed
- Quick action buttons

---

## Application Structure

### Available Pages

| Page | URL | Features |
|------|-----|----------|
| **Home** | `http://localhost:3001/` | Personalized feed, AI recommendations, social activity |
| **Discover** | `http://localhost:3001/discover` | Search venues, browse grid, filters |
| **Bookings** | `http://localhost:3001/bookings` | Upcoming/past bookings, confirmation codes |
| **Social** | `http://localhost:3001/social` | Social features (placeholder) |

### Navigation

Use the **bottom navigation bar** to switch between pages:
- 🏠 Home
- 🔍 Discover
- 📅 Bookings
- 👥 Social

---

## Troubleshooting

### Issue: "Cannot connect to API"

**Solution:**
```bash
# Check if backend is running
curl http://localhost:8000/api/v1/users/1

# Should return user data
```

### Issue: "No recommendations shown"

**Possible causes:**
1. Backend not running
2. Data not seeded
3. User ID 1 doesn't exist

**Solution:**
```bash
# Seed data again
curl -X POST http://localhost:8000/api/v1/admin/data/seed

# Verify user exists
curl http://localhost:8000/api/v1/users/1
```

### Issue: "Module not found errors"

**Solution:**
```bash
cd user-app
rm -rf node_modules package-lock.json
npm install
```

### Issue: "Port 3001 already in use"

**Solution:**
```bash
# Find process using port 3001
lsof -i :3001

# Kill the process
kill -9 <PID>

# Or use different port
npm run dev -- -p 3002
```

### Issue: "Page shows loading forever"

**Check:**
1. Backend API is running: `curl http://localhost:8000/health`
2. CORS is enabled in backend
3. Browser console for errors (F12)

**Solution:**
```bash
# Restart both services
# Terminal 1: Backend
cd backend
uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd user-app
npm run dev
```

---

## Testing the User View

### 1. View Personalized Recommendations
1. Go to Home (`/`)
2. You should see:
   - Hero recommendation card with AI explanation
   - Match score percentage
   - Secondary recommendations
3. Click on any venue card

### 2. Search for Venues
1. Navigate to Discover (`/discover`)
2. Type in search box: "Italian" or "Mexican"
3. Click Search
4. Browse results grid

### 3. Check Bookings
1. Navigate to Bookings (`/bookings`)
2. View upcoming bookings (if any)
3. See confirmation codes
4. Check past bookings

### 4. Real-time Updates
1. Keep User View open on Home page
2. In another tab, open Admin Dashboard (`http://localhost:3000`)
3. Start simulation
4. Watch recommendations update in User View (every 30s)

---

## Architecture Overview

```
User View (Port 3001)
       ↓
  API Calls
       ↓
Backend API (Port 8000)
       ↓
   Database
```

### API Endpoints Used

- `GET /api/v1/users/{id}` - Get user info
- `GET /api/v1/recommendations/user/{id}` - Get recommendations
- `GET /api/v1/venues/search` - Search venues
- `GET /api/v1/bookings/user/{id}` - Get bookings
- `SSE /api/v1/admin/streams/subscribe/recommendations` - Real-time updates

---

## Demo Flow

### Scenario 1: First-Time User Experience
1. Open `http://localhost:3001`
2. See personalized recommendations immediately
3. View AI explanations for recommendations
4. Check social activity feed
5. Explore quick actions

### Scenario 2: Venue Discovery
1. Click Discover in navigation
2. Search for cuisine type
3. Apply filters (trending, open now)
4. Click venue to view details (coming soon)

### Scenario 3: Booking Management
1. Click Bookings in navigation
2. View upcoming reservations
3. See confirmation codes
4. Check past bookings

---

## Switching Users

The app defaults to **User ID 1**. To test with different users:

### Option 1: Edit Code
```typescript
// Edit: user-app/app/page.tsx
const DEFAULT_USER_ID = 2  // Change from 1 to any user ID
```

### Option 2: Dynamic Selection (Future Enhancement)
Implement user login/selection screen

---

## Environment Configuration

### Optional: Create `.env.local`

```bash
# In user-app directory
cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_URL=ws://localhost:8000
EOF
```

---

## Complete Setup Script

```bash
#!/bin/bash

# Setup everything in one go
echo "🚀 Starting Luna Social User View Setup..."

# 1. Start Backend
echo "📡 Starting Backend..."
cd /home/ubuntu/ETC/Luna_assignemnt/luna_assignment/backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!
sleep 5

# 2. Seed Data
echo "🌱 Seeding data..."
curl -X POST http://localhost:8000/api/v1/admin/data/seed

# 3. Install and Start User View
echo "💻 Setting up User View..."
cd /home/ubuntu/ETC/Luna_assignemnt/luna_assignment/user-app
npm install
npm run dev &
USER_APP_PID=$!

echo "✅ Setup complete!"
echo ""
echo "📱 User View: http://localhost:3001"
echo "🔧 Admin Dashboard: http://localhost:3000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Keep script running
wait
```

Save as `start-user-view.sh` and run:
```bash
chmod +x start-user-view.sh
./start-user-view.sh
```

---

## System Requirements

- **OS**: Linux, macOS, Windows (WSL recommended)
- **Node.js**: 18.0.0 or higher
- **RAM**: 2GB minimum
- **Disk**: 500MB for dependencies

---

## Next Steps

Once the User View is running:

1. ✅ Test all pages and navigation
2. ✅ Verify API integration
3. ✅ Check real-time updates
4. ✅ Test on mobile view (responsive)
5. ✅ Compare with Admin Dashboard for demo

---

## Demo Presentation Flow

### Three-Window Setup
1. **Window 1**: User View (`http://localhost:3001`)
2. **Window 2**: Admin Dashboard (`http://localhost:3000`)
3. **Window 3**: API Docs (`http://localhost:8000/docs`)

### Demo Script
1. Show Admin Dashboard - system intelligence
2. Start simulation with scenario
3. Switch to User View - customer experience
4. Show personalized recommendations updating
5. Demonstrate booking flow
6. Show social features

---

**Status**: ✅ User View is ready to run!
**Support**: Check `USER_VIEW_STATUS.md` for implementation details

