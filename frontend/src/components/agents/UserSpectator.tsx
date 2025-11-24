/**
 * UserSpectator - User selector and context panel for Recommendation Agent View
 */
import { User as UserIcon, MapPin, Clock, TrendingUp } from 'lucide-react'
import { User, RecommendationContext } from '../../types/agent'

interface UserSpectatorProps {
  users: User[]
  selectedUserId: number | null
  onSelectUser: (userId: number) => void
  context: RecommendationContext | null
  currentActivity?: string
}

const personaBadgeColors: Record<string, string> = {
  'social_butterfly': 'bg-pink-100 text-pink-700 border-pink-300',
  'foodie_explorer': 'bg-orange-100 text-orange-700 border-orange-300',
  'routine_regular': 'bg-blue-100 text-blue-700 border-blue-300',
  'event_organizer': 'bg-purple-100 text-purple-700 border-purple-300',
  'spontaneous_diner': 'bg-yellow-100 text-yellow-700 border-yellow-300',
  'busy_professional': 'bg-gray-100 text-gray-700 border-gray-300',
  'budget_conscious': 'bg-green-100 text-green-700 border-green-300',
}

export function UserSpectator({
  users,
  selectedUserId,
  onSelectUser,
  context,
  currentActivity,
}: UserSpectatorProps) {
  const selectedUser = users.find((u) => u.id === selectedUserId)

  const formatPersona = (persona: string) => {
    return persona.split('_').map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')
  }

  const getMealTimeEmoji = (mealTime: string) => {
    const emojis: Record<string, string> = {
      breakfast: '🌅',
      lunch: '☀️',
      afternoon: '🌤️',
      dinner: '🌆',
      late_night: '🌙',
    }
    return emojis[mealTime] || '🍽️'
  }

  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 sticky top-4">
      <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
        <UserIcon className="w-5 h-5" />
        User Spectator
      </h3>

      {/* User Selector */}
      <div className="mb-6">
        <label className="text-sm text-gray-500 mb-2 block">Select User to Watch</label>
        <select
          value={selectedUserId || ''}
          onChange={(e) => onSelectUser(Number(e.target.value))}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
        >
          <option value="">Select a user...</option>
          {users.map((user) => (
            <option key={user.id} value={user.id}>
              {user.username} {user.persona ? `(${formatPersona(user.persona)})` : ''}
            </option>
          ))}
        </select>
      </div>

      {/* Selected User Info */}
      {selectedUser && (
        <>
          <div className="mb-4 p-4 bg-gradient-to-r from-indigo-50 to-purple-50 rounded-lg border border-indigo-200">
            <div className="flex items-start justify-between mb-2">
              <div>
                <h4 className="font-semibold text-gray-900">{selectedUser.username}</h4>
                <p className="text-sm text-gray-500">ID: {selectedUser.id}</p>
              </div>
              {selectedUser.persona && (
                <span
                  className={`px-3 py-1 rounded-full text-xs font-medium border ${
                    personaBadgeColors[selectedUser.persona] || 'bg-gray-100 text-gray-700'
                  }`}
                >
                  {formatPersona(selectedUser.persona)}
                </span>
              )}
            </div>
            {currentActivity && (
              <div className="flex items-center gap-2 mt-2 text-sm">
                <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                <span className="text-gray-600">{currentActivity}</span>
              </div>
            )}
          </div>

          {/* Context Dashboard */}
          {context && (
            <div className="space-y-3">
              <h4 className="text-sm font-semibold text-gray-700 mb-2">Current Context</h4>

              {/* Time Context */}
              <div className="flex items-center gap-3 p-3 bg-blue-50 rounded-lg">
                <Clock className="w-5 h-5 text-blue-600" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900">
                    {getMealTimeEmoji(context.meal_time)} {context.meal_time.charAt(0).toUpperCase() + context.meal_time.slice(1)}
                  </p>
                  <p className="text-xs text-gray-500">
                    {context.is_weekend ? 'Weekend' : 'Weekday'} • {context.hour}:00
                  </p>
                </div>
              </div>

              {/* Location Context */}
              {context.user_location && (
                <div className="flex items-center gap-3 p-3 bg-green-50 rounded-lg">
                  <MapPin className="w-5 h-5 text-green-600" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">Location</p>
                    <p className="text-xs text-gray-500 font-mono">
                      {context.user_location.lat.toFixed(4)}, {context.user_location.lon.toFixed(4)}
                    </p>
                  </div>
                </div>
              )}

              {/* Preferences */}
              <div className="p-3 bg-purple-50 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <TrendingUp className="w-4 h-4 text-purple-600" />
                  <p className="text-sm font-medium text-gray-900">Preferences</p>
                </div>
                <div className="space-y-1 text-xs">
                  {context.preferences.cuisines.length > 0 && (
                    <p className="text-gray-600">
                      <span className="font-medium">Cuisines:</span>{' '}
                      {context.preferences.cuisines.slice(0, 3).join(', ')}
                      {context.preferences.cuisines.length > 3 && ` +${context.preferences.cuisines.length - 3}`}
                    </p>
                  )}
                  <p className="text-gray-600">
                    <span className="font-medium">Price:</span> $
                    {context.preferences.price_range[0]} - ${context.preferences.price_range[1]}
                  </p>
                  <p className="text-gray-600">
                    <span className="font-medium">Max Distance:</span> {context.preferences.max_distance} km
                  </p>
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {!selectedUser && (
        <div className="text-center py-8">
          <UserIcon className="w-12 h-12 text-gray-300 mx-auto mb-2" />
          <p className="text-sm text-gray-400">Select a user to view their context</p>
        </div>
      )}
    </div>
  )
}

