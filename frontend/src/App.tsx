import { useState, useEffect, useCallback } from 'react'
import {
  Play, Pause, RotateCcw, Zap, Users, MapPin, Calendar,
  TrendingUp, Activity, Clock, ChevronRight, Settings
} from 'lucide-react'
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts'

// Types
interface SimulationState {
  running: boolean
  paused: boolean
  simulation_time: string
  speed_multiplier: number
  scenario: string
  events_generated: number
  bookings_created: number
  invites_sent: number
  active_users: number
}

interface StreamEvent {
  event_type: string
  channel: string
  payload: Record<string, unknown>
  simulation_time: string
  user_id?: number
  venue_id?: number
}

interface Stats {
  users: { total: number; simulated: number; real: number }
  venues: { total: number; trending: number }
  bookings: { total: number; confirmed: number }
}

// API configuration
const API_BASE = '/api/v1'

// API helpers
async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  })
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}

// Components
function StatCard({ icon: Icon, title, value, subtitle, trend }: {
  icon: React.ElementType
  title: string
  value: string | number
  subtitle?: string
  trend?: 'up' | 'down' | 'neutral'
}) {
  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-gray-500 font-medium">{title}</p>
          <p className="text-3xl font-bold text-gray-900 mt-1">{value}</p>
          {subtitle && (
            <p className="text-sm text-gray-400 mt-1">{subtitle}</p>
          )}
        </div>
        <div className={`p-3 rounded-lg ${
          trend === 'up' ? 'bg-green-100' :
          trend === 'down' ? 'bg-red-100' : 'bg-indigo-100'
        }`}>
          <Icon className={`w-6 h-6 ${
            trend === 'up' ? 'text-green-600' :
            trend === 'down' ? 'text-red-600' : 'text-indigo-600'
          }`} />
        </div>
      </div>
    </div>
  )
}

function SimulationControls({ state, onStart, onPause, onResume, onStop, onReset, onSpeedChange, onScenarioChange }: {
  state: SimulationState
  onStart: () => void
  onPause: () => void
  onResume: () => void
  onStop: () => void
  onReset: () => void
  onSpeedChange: (speed: number) => void
  onScenarioChange: (scenario: string) => void
}) {
  const scenarios = [
    { id: 'normal', name: 'Normal Day' },
    { id: 'lunch_rush', name: 'Lunch Rush' },
    { id: 'friday_night', name: 'Friday Night' },
    { id: 'weekend_brunch', name: 'Weekend Brunch' },
  ]

  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Simulation Control</h3>
        <div className={`flex items-center gap-2 px-3 py-1 rounded-full text-sm ${
          state.running && !state.paused
            ? 'bg-green-100 text-green-700'
            : state.paused
            ? 'bg-yellow-100 text-yellow-700'
            : 'bg-gray-100 text-gray-600'
        }`}>
          <span className={`w-2 h-2 rounded-full ${
            state.running && !state.paused
              ? 'bg-green-500 animate-pulse'
              : state.paused
              ? 'bg-yellow-500'
              : 'bg-gray-400'
          }`} />
          {state.running && !state.paused ? 'Running' : state.paused ? 'Paused' : 'Stopped'}
        </div>
      </div>

      {/* Control Buttons */}
      <div className="flex gap-2 mb-4">
        {!state.running ? (
          <button
            onClick={onStart}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
          >
            <Play className="w-4 h-4" />
            Start
          </button>
        ) : state.paused ? (
          <button
            onClick={onResume}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
          >
            <Play className="w-4 h-4" />
            Resume
          </button>
        ) : (
          <button
            onClick={onPause}
            className="flex items-center gap-2 px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition-colors"
          >
            <Pause className="w-4 h-4" />
            Pause
          </button>
        )}
        <button
          onClick={onStop}
          disabled={!state.running}
          className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50"
        >
          Stop
        </button>
        <button
          onClick={onReset}
          className="flex items-center gap-2 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
        >
          <RotateCcw className="w-4 h-4" />
          Reset
        </button>
      </div>

      {/* Speed Control */}
      <div className="mb-4">
        <label className="text-sm text-gray-500 mb-2 block">Speed Multiplier</label>
        <div className="flex gap-2">
          {[1, 5, 10, 25, 50].map((speed) => (
            <button
              key={speed}
              onClick={() => onSpeedChange(speed)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                state.speed_multiplier === speed
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {speed}x
            </button>
          ))}
        </div>
      </div>

      {/* Scenario Selection */}
      <div>
        <label className="text-sm text-gray-500 mb-2 block">Scenario</label>
        <div className="grid grid-cols-2 gap-2">
          {scenarios.map((scenario) => (
            <button
              key={scenario.id}
              onClick={() => onScenarioChange(scenario.id)}
              className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors text-left ${
                state.scenario === scenario.id
                  ? 'bg-indigo-100 text-indigo-700 border-2 border-indigo-300'
                  : 'bg-gray-50 text-gray-600 hover:bg-gray-100 border-2 border-transparent'
              }`}
            >
              {scenario.name}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

function EventFeed({ events }: { events: StreamEvent[] }) {
  const getEventColor = (type: string) => {
    if (type.includes('booking')) return 'border-green-400 bg-green-50'
    if (type.includes('invite') || type.includes('social')) return 'border-purple-400 bg-purple-50'
    if (type.includes('recommendation')) return 'border-blue-400 bg-blue-50'
    if (type.includes('simulation')) return 'border-yellow-400 bg-yellow-50'
    return 'border-gray-400 bg-gray-50'
  }

  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 h-full">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Live Event Feed</h3>
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {events.length === 0 ? (
          <p className="text-gray-400 text-center py-8">
            No events yet. Start the simulation to see live activity.
          </p>
        ) : (
          events.map((event, idx) => (
            <div
              key={idx}
              className={`p-3 rounded-lg border-l-4 animate-slide-up ${getEventColor(event.event_type)}`}
            >
              <div className="flex justify-between items-start">
                <span className="font-medium text-gray-800 text-sm">
                  {event.event_type.replace(/_/g, ' ')}
                </span>
                <span className="text-xs text-gray-400">
                  {new Date(event.simulation_time).toLocaleTimeString()}
                </span>
              </div>
              {event.user_id && (
                <p className="text-xs text-gray-500 mt-1">User #{event.user_id}</p>
              )}
              {event.venue_id && (
                <p className="text-xs text-gray-500">Venue #{event.venue_id}</p>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  )
}

function MetricsChart({ data }: { data: { time: string; events: number; bookings: number }[] }) {
  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Activity Over Time</h3>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="time" stroke="#9ca3af" fontSize={12} />
            <YAxis stroke="#9ca3af" fontSize={12} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#fff',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
              }}
            />
            <Area
              type="monotone"
              dataKey="events"
              stroke="#6366f1"
              fill="#6366f1"
              fillOpacity={0.2}
              name="Events"
            />
            <Area
              type="monotone"
              dataKey="bookings"
              stroke="#10b981"
              fill="#10b981"
              fillOpacity={0.2}
              name="Bookings"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

// Main App
export default function App() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [simState, setSimState] = useState<SimulationState>({
    running: false,
    paused: false,
    simulation_time: new Date().toISOString(),
    speed_multiplier: 1,
    scenario: 'normal',
    events_generated: 0,
    bookings_created: 0,
    invites_sent: 0,
    active_users: 0,
  })
  const [events, setEvents] = useState<StreamEvent[]>([])
  const [chartData, setChartData] = useState<{ time: string; events: number; bookings: number }[]>([])
  const [loading, setLoading] = useState(true)
  const [seeding, setSeeding] = useState(false)

  // Fetch initial stats
  useEffect(() => {
    fetchAPI<Stats>('/admin/stats')
      .then(setStats)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  // Poll simulation state
  useEffect(() => {
    const interval = setInterval(() => {
      if (simState.running) {
        fetchAPI<SimulationState>('/simulation/metrics')
          .then((state) => {
            setSimState(state)
            // Update chart data
            setChartData((prev) => [
              ...prev.slice(-20),
              {
                time: new Date().toLocaleTimeString(),
                events: state.events_generated,
                bookings: state.bookings_created,
              },
            ])
          })
          .catch(console.error)
      }
    }, 1000)

    return () => clearInterval(interval)
  }, [simState.running])

  // SSE event subscription
  useEffect(() => {
    if (!simState.running) return

    const eventSource = new EventSource(`${API_BASE}/admin/streams/subscribe-all`)

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.event_type && data.event_type !== 'metrics_update') {
          setEvents((prev) => [data, ...prev].slice(0, 50))
        }
      } catch {
        // Ignore parse errors
      }
    }

    eventSource.onerror = () => {
      console.error('SSE connection error')
    }

    return () => eventSource.close()
  }, [simState.running])

  // Control handlers
  const handleStart = useCallback(async () => {
    await fetchAPI('/simulation/start', {
      method: 'POST',
      body: JSON.stringify({ speed: simState.speed_multiplier, scenario: simState.scenario }),
    })
    setSimState((s) => ({ ...s, running: true, paused: false }))
  }, [simState.speed_multiplier, simState.scenario])

  const handlePause = useCallback(async () => {
    await fetchAPI('/simulation/pause', { method: 'POST' })
    setSimState((s) => ({ ...s, paused: true }))
  }, [])

  const handleResume = useCallback(async () => {
    await fetchAPI('/simulation/resume', { method: 'POST' })
    setSimState((s) => ({ ...s, paused: false }))
  }, [])

  const handleStop = useCallback(async () => {
    await fetchAPI('/simulation/stop', { method: 'POST' })
    setSimState((s) => ({ ...s, running: false, paused: false }))
  }, [])

  const handleReset = useCallback(async () => {
    await fetchAPI('/simulation/reset', { method: 'POST' })
    setSimState({
      running: false,
      paused: false,
      simulation_time: new Date().toISOString(),
      speed_multiplier: 1,
      scenario: 'normal',
      events_generated: 0,
      bookings_created: 0,
      invites_sent: 0,
      active_users: 0,
    })
    setEvents([])
    setChartData([])
  }, [])

  const handleSpeedChange = useCallback(async (speed: number) => {
    await fetchAPI('/simulation/speed', {
      method: 'POST',
      body: JSON.stringify({ multiplier: speed }),
    })
    setSimState((s) => ({ ...s, speed_multiplier: speed }))
  }, [])

  const handleScenarioChange = useCallback(async (scenario: string) => {
    await fetchAPI('/simulation/scenario', {
      method: 'POST',
      body: JSON.stringify({ scenario }),
    })
    setSimState((s) => ({ ...s, scenario }))
  }, [])

  const handleSeedData = useCallback(async () => {
    setSeeding(true)
    try {
      await fetchAPI('/admin/data/seed?user_count=50', { method: 'POST' })
      const newStats = await fetchAPI<Stats>('/admin/stats')
      setStats(newStats)
    } finally {
      setSeeding(false)
    }
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center">
              <span className="text-white font-bold text-xl">L</span>
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">Luna Social</h1>
              <p className="text-sm text-gray-500">Admin Dashboard</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={handleSeedData}
              disabled={seeding}
              className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors disabled:opacity-50"
            >
              {seeding ? 'Seeding...' : 'Seed Demo Data'}
            </button>
            <div className="flex items-center gap-2 text-sm text-gray-500">
              <Clock className="w-4 h-4" />
              {new Date(simState.simulation_time).toLocaleString()}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <StatCard
            icon={Users}
            title="Total Users"
            value={stats?.users.total || 0}
            subtitle={`${stats?.users.simulated || 0} simulated`}
            trend="neutral"
          />
          <StatCard
            icon={MapPin}
            title="Venues"
            value={stats?.venues.total || 0}
            subtitle={`${stats?.venues.trending || 0} trending`}
            trend="up"
          />
          <StatCard
            icon={Calendar}
            title="Bookings"
            value={simState.bookings_created || stats?.bookings.total || 0}
            subtitle="Total created"
            trend="up"
          />
          <StatCard
            icon={Activity}
            title="Events Generated"
            value={simState.events_generated}
            subtitle={`${simState.active_users} active users`}
            trend="neutral"
          />
        </div>

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Controls */}
          <div className="space-y-6">
            <SimulationControls
              state={simState}
              onStart={handleStart}
              onPause={handlePause}
              onResume={handleResume}
              onStop={handleStop}
              onReset={handleReset}
              onSpeedChange={handleSpeedChange}
              onScenarioChange={handleScenarioChange}
            />

            {/* Quick Stats */}
            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Simulation Metrics</h3>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-gray-500">Events Generated</span>
                  <span className="font-semibold text-gray-900">{simState.events_generated}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-500">Bookings Created</span>
                  <span className="font-semibold text-green-600">{simState.bookings_created}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-500">Invites Sent</span>
                  <span className="font-semibold text-purple-600">{simState.invites_sent}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-500">Active Users</span>
                  <span className="font-semibold text-blue-600">{simState.active_users}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Middle Column - Chart */}
          <div className="lg:col-span-2 space-y-6">
            <MetricsChart data={chartData} />
            <EventFeed events={events} />
          </div>
        </div>
      </main>
    </div>
  )
}
