/**
 * Booking Density Chart - Shows booking distribution over time.
 */
import { useState, useEffect } from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts'

interface BookingData {
  hour: string
  bookings: number
  invites: number
}

interface StreamEvent {
  event_type: string
  channel: string
  simulation_time: string
}

export function BookingDensity({ events }: { events: StreamEvent[] }) {
  const [data, setData] = useState<BookingData[]>([])

  useEffect(() => {
    // Initialize hours
    const hours: Record<string, { bookings: number; invites: number }> = {}
    for (let i = 0; i < 24; i++) {
      const hour = i.toString().padStart(2, '0') + ':00'
      hours[hour] = { bookings: 0, invites: 0 }
    }

    // Count events by hour
    events.forEach((event) => {
      try {
        const date = new Date(event.simulation_time)
        const hour = date.getHours().toString().padStart(2, '0') + ':00'

        if (hours[hour]) {
          if (event.event_type.includes('booking')) {
            hours[hour].bookings++
          } else if (event.event_type.includes('invite')) {
            hours[hour].invites++
          }
        }
      } catch (e) {
        // Ignore invalid dates
      }
    })

    // Convert to array
    const chartData = Object.entries(hours).map(([hour, counts]) => ({
      hour,
      bookings: counts.bookings,
      invites: counts.invites,
    }))

    setData(chartData)
  }, [events])

  const getBarColor = (hour: string) => {
    const h = parseInt(hour.split(':')[0], 10)
    // Lunch hours (11-14) and dinner hours (18-21) get highlighted
    if ((h >= 11 && h <= 14) || (h >= 18 && h <= 21)) {
      return '#6366f1' // indigo
    }
    return '#a5b4fc' // lighter indigo
  }

  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        Activity by Hour
      </h3>
      <div className="h-48">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="hour"
              stroke="#9ca3af"
              fontSize={10}
              interval={2}
              tickFormatter={(v) => v.split(':')[0]}
            />
            <YAxis stroke="#9ca3af" fontSize={10} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#fff',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
                fontSize: '12px',
              }}
              formatter={(value: number, name: string) => [
                value,
                name.charAt(0).toUpperCase() + name.slice(1),
              ]}
            />
            <Bar dataKey="bookings" name="bookings" radius={[2, 2, 0, 0]}>
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={getBarColor(entry.hour)} />
              ))}
            </Bar>
            <Bar
              dataKey="invites"
              name="invites"
              fill="#a855f7"
              radius={[2, 2, 0, 0]}
              opacity={0.7}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="flex justify-center gap-6 mt-4 text-xs">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-indigo-500" />
          <span className="text-gray-600">Bookings</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-purple-500" />
          <span className="text-gray-600">Invites</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-indigo-300" />
          <span className="text-gray-600">Off-peak</span>
        </div>
      </div>
    </div>
  )
}

export default BookingDensity
