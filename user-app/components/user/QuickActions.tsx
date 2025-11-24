'use client'

import { Search, Users, Calendar, Star, MapPin } from 'lucide-react'
import { useRouter } from 'next/navigation'

export function QuickActions() {
  const router = useRouter()
  const hour = new Date().getHours()
  
  const getTimeBasedAction = () => {
    if (hour >= 6 && hour < 11) return { label: 'Find Breakfast', icon: '🍳' }
    if (hour >= 11 && hour < 15) return { label: 'Quick Lunch', icon: '🍔' }
    if (hour >= 15 && hour < 18) return { label: 'Afternoon Bites', icon: '☕' }
    if (hour >= 18 && hour < 22) return { label: "Tonight's Hot Spots", icon: '🌙' }
    return { label: 'Late Night Eats', icon: '🌃' }
  }

  const timeAction = getTimeBasedAction()

  const actions = [
    { icon: Search, label: 'Browse All', path: '/discover', color: 'from-purple-500 to-purple-600' },
    { icon: Users, label: 'Find Partners', path: '/social', color: 'from-orange-500 to-orange-600' },
    { icon: Calendar, label: 'My Bookings', path: '/bookings', color: 'from-blue-500 to-blue-600' },
    { icon: Star, label: 'Reviews', path: '/reviews', color: 'from-green-500 to-green-600' },
  ]

  return (
    <div className="space-y-4">
      {/* Time-based CTA */}
      <div 
        className="bg-gradient-to-r from-purple-600 to-orange-600 rounded-xl p-6 text-white cursor-pointer hover:shadow-lg transition-shadow"
        onClick={() => router.push('/discover')}
      >
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm opacity-90 mb-1">Quick Action</p>
            <p className="text-xl font-bold flex items-center gap-2">
              <span>{timeAction.icon}</span>
              {timeAction.label}
            </p>
          </div>
          <MapPin className="w-8 h-8 opacity-80" />
        </div>
      </div>

      {/* Action Grid */}
      <div className="grid grid-cols-2 gap-3">
        {actions.map((action) => {
          const Icon = action.icon
          return (
            <button
              key={action.path}
              onClick={() => router.push(action.path)}
              className={`bg-gradient-to-r ${action.color} rounded-xl p-4 text-white hover:shadow-lg transition-all transform hover:scale-105`}
            >
              <Icon className="w-6 h-6 mb-2" />
              <p className="text-sm font-semibold">{action.label}</p>
            </button>
          )
        })}
      </div>
    </div>
  )
}

