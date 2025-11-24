'use client'

import { User } from '@/lib/api-client'
import { Bell, Settings, Users } from 'lucide-react'

interface UserHeaderProps {
  user: User
  friendCount?: number
  upcomingBookingsCount?: number
}

export function UserHeader({ user, friendCount = 0, upcomingBookingsCount = 0 }: UserHeaderProps) {
  const personaColors: Record<string, string> = {
    'Social Butterfly': 'bg-pink-100 text-pink-700',
    'Foodie Explorer': 'bg-orange-100 text-orange-700',
    'Routine Regular': 'bg-blue-100 text-blue-700',
    'Event Organizer': 'bg-purple-100 text-purple-700',
    'Spontaneous Diner': 'bg-green-100 text-green-700',
    'Busy Professional': 'bg-gray-100 text-gray-700',
  }

  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          {/* User Info */}
          <div className="flex items-center gap-4">
            <div className="relative">
              <div className="w-12 h-12 rounded-full bg-gradient-to-br from-purple-500 to-orange-500 flex items-center justify-center text-white font-bold text-lg">
                {user.username.charAt(0).toUpperCase()}
              </div>
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">{user.username}</h1>
              {user.persona && (
                <span className={`inline-block px-2 py-1 rounded-full text-xs font-semibold ${
                  personaColors[user.persona] || 'bg-gray-100 text-gray-700'
                }`}>
                  {user.persona}
                </span>
              )}
            </div>
          </div>

          {/* Quick Stats */}
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <Users className="w-4 h-4" />
              <span className="font-semibold">{friendCount}</span>
            </div>
            {upcomingBookingsCount > 0 && (
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <span className="font-semibold">{upcomingBookingsCount}</span>
                <span>upcoming</span>
              </div>
            )}
            <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
              <Bell className="w-5 h-5 text-gray-600" />
            </button>
            <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
              <Settings className="w-5 h-5 text-gray-600" />
            </button>
          </div>
        </div>
      </div>
    </header>
  )
}

