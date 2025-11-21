/**
 * Environment Panel - Shows weather, traffic, and special events.
 */
import { useState, useEffect } from 'react'
import { Cloud, Sun, CloudRain, Wind, Car, Calendar } from 'lucide-react'

interface EnvironmentContext {
  weather: {
    condition: string
    temperature: number
    humidity: number
    wind_speed: number
  }
  traffic: {
    level: string
    delay_minutes: number
  }
  special_events: Array<{
    type: string
    name: string
    start_time: string
    expected_attendance: number
  }>
  timestamp: string
}

interface TemporalContext {
  context: {
    hour: number
    day_of_week: number
    meal_period: string
    is_weekend: boolean
    is_holiday: boolean
    holiday_name: string | null
    season: string
  }
  modifiers: Record<string, number>
  recommended_scenarios: string[]
}

const API_BASE = '/api/v1'

function WeatherIcon({ condition }: { condition: string }) {
  switch (condition) {
    case 'sunny':
      return <Sun className="w-8 h-8 text-yellow-500" />
    case 'rainy':
      return <CloudRain className="w-8 h-8 text-blue-500" />
    case 'cloudy':
      return <Cloud className="w-8 h-8 text-gray-400" />
    case 'windy':
      return <Wind className="w-8 h-8 text-teal-500" />
    default:
      return <Sun className="w-8 h-8 text-yellow-500" />
  }
}

function TrafficIndicator({ level }: { level: string }) {
  const colors = {
    low: 'bg-green-500',
    medium: 'bg-yellow-500',
    high: 'bg-orange-500',
    severe: 'bg-red-500',
  }

  return (
    <div className="flex items-center gap-2">
      <Car className="w-5 h-5 text-gray-600" />
      <div className="flex gap-1">
        {['low', 'medium', 'high', 'severe'].map((l) => (
          <div
            key={l}
            className={`w-2 h-4 rounded ${
              ['low', 'medium', 'high', 'severe'].indexOf(l) <=
              ['low', 'medium', 'high', 'severe'].indexOf(level)
                ? colors[level as keyof typeof colors] || 'bg-gray-300'
                : 'bg-gray-200'
            }`}
          />
        ))}
      </div>
      <span className="text-sm capitalize text-gray-600">{level}</span>
    </div>
  )
}

export function EnvironmentPanel() {
  const [envContext, setEnvContext] = useState<EnvironmentContext | null>(null)
  const [temporal, setTemporal] = useState<TemporalContext | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchEnvironment = async () => {
      try {
        const [envRes, tempRes] = await Promise.all([
          fetch(`${API_BASE}/admin/environment/context`),
          fetch(`${API_BASE}/admin/environment/temporal`),
        ])

        if (envRes.ok) {
          setEnvContext(await envRes.json())
        }
        if (tempRes.ok) {
          setTemporal(await tempRes.json())
        }
      } catch (e) {
        console.error('Failed to fetch environment:', e)
      } finally {
        setLoading(false)
      }
    }

    fetchEnvironment()

    // Refresh every 30 seconds
    const interval = setInterval(fetchEnvironment, 30000)
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4" />
          <div className="h-20 bg-gray-200 rounded" />
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Environment</h3>

      <div className="grid grid-cols-2 gap-4">
        {/* Weather */}
        {envContext && (
          <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg p-4">
            <div className="flex items-center gap-3">
              <WeatherIcon condition={envContext.weather.condition} />
              <div>
                <p className="text-2xl font-bold text-gray-900">
                  {Math.round(envContext.weather.temperature)}°F
                </p>
                <p className="text-sm text-gray-500 capitalize">
                  {envContext.weather.condition}
                </p>
              </div>
            </div>
            <div className="mt-2 text-xs text-gray-500">
              Humidity: {Math.round(envContext.weather.humidity)}%
            </div>
          </div>
        )}

        {/* Traffic */}
        {envContext && (
          <div className="bg-gradient-to-br from-gray-50 to-slate-50 rounded-lg p-4">
            <p className="text-sm font-medium text-gray-700 mb-2">Traffic</p>
            <TrafficIndicator level={envContext.traffic.level} />
            <p className="text-xs text-gray-500 mt-2">
              ~{Math.round(envContext.traffic.delay_minutes)} min delay
            </p>
          </div>
        )}
      </div>

      {/* Temporal Context */}
      {temporal && (
        <div className="mt-4 pt-4 border-t border-gray-100">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-500">Meal Period</span>
            <span className="font-medium capitalize text-gray-900">
              {temporal.context.meal_period}
            </span>
          </div>
          <div className="flex items-center justify-between text-sm mt-2">
            <span className="text-gray-500">Season</span>
            <span className="font-medium capitalize text-gray-900">
              {temporal.context.season}
            </span>
          </div>
          {temporal.context.is_holiday && temporal.context.holiday_name && (
            <div className="flex items-center gap-2 mt-2 text-sm text-purple-600">
              <Calendar className="w-4 h-4" />
              {temporal.context.holiday_name}
            </div>
          )}
          {temporal.context.is_weekend && (
            <div className="mt-2 px-2 py-1 bg-indigo-100 text-indigo-700 text-xs rounded-full inline-block">
              Weekend
            </div>
          )}
        </div>
      )}

      {/* Special Events */}
      {envContext && envContext.special_events.length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-100">
          <p className="text-sm font-medium text-gray-700 mb-2">Special Events</p>
          {envContext.special_events.map((event, idx) => (
            <div
              key={idx}
              className="bg-yellow-50 border border-yellow-200 rounded-lg p-2 text-sm"
            >
              <p className="font-medium text-yellow-800">{event.name}</p>
              <p className="text-xs text-yellow-600">
                {event.expected_attendance.toLocaleString()} expected
              </p>
            </div>
          ))}
        </div>
      )}

      {/* Recommended Scenarios */}
      {temporal && temporal.recommended_scenarios.length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-100">
          <p className="text-xs text-gray-500 mb-2">Recommended scenarios:</p>
          <div className="flex flex-wrap gap-1">
            {temporal.recommended_scenarios.map((scenario) => (
              <span
                key={scenario}
                className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded"
              >
                {scenario.replace(/_/g, ' ')}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default EnvironmentPanel
