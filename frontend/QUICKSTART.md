# Frontend Quick Start Guide

Get the Luna Social Admin Dashboard running in under 2 minutes.

## Prerequisites

- **Node.js** 18+ (check with `node --version`)
- **npm** 9+ (check with `npm --version`)

## Quick Start

```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Start development server
npm run dev
```

The dashboard will be available at **http://localhost:3000**

## Available Commands

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server with hot reload |
| `npm run build` | Build production bundle |
| `npm run preview` | Preview production build locally |
| `npm run lint` | Run ESLint for code quality |

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool & dev server
- **Tailwind CSS** - Styling
- **Recharts** - Data visualization
- **React Leaflet** - Maps
- **React Force Graph** - Social graph visualization

## Project Structure

```
frontend/
├── src/
│   ├── App.tsx              # Main dashboard component
│   ├── main.tsx             # Entry point
│   ├── index.css            # Global styles (Tailwind)
│   ├── components/          # React components
│   │   ├── SocialGraph.tsx      # Social network visualization
│   │   ├── BookingDensity.tsx   # Booking heatmap
│   │   └── EnvironmentPanel.tsx # Environment controls
│   └── hooks/
│       └── useWebSocket.ts  # WebSocket hook for real-time updates
├── package.json
├── vite.config.ts           # Vite configuration
├── tsconfig.json            # TypeScript config
└── tailwind.config.js       # Tailwind CSS config
```

## API Proxy

The development server automatically proxies API requests:
- `/api/*` → `http://localhost:8000`

Make sure the backend is running on port 8000 for full functionality.

## Environment

No environment variables required for development. The Vite config handles:
- Dev server port: 3000
- API proxy to backend: localhost:8000

## Troubleshooting

### Port 3000 already in use
```bash
# Find and kill the process
lsof -i :3000
kill -9 <PID>
```

### Dependencies issues
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

### TypeScript errors
```bash
# Check types without building
npx tsc --noEmit
```

### Backend not connected
Make sure the backend is running:
```bash
cd ../backend
uvicorn app.main:app --reload --port 8000
```

## Next Steps

1. Start the backend server (see `backend/QUICKSTART.md`)
2. Seed the database: `POST http://localhost:8000/api/v1/admin/data/seed`
3. Start a simulation: `POST http://localhost:8000/api/v1/simulation/start`
4. Watch the dashboard come alive with real-time data!
