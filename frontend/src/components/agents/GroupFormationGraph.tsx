/**
 * GroupFormationGraph - Visual node graph for booking group formation
 */
import { User, MapPin, Check, X, Clock } from 'lucide-react'
import { BookingData } from '../../types/agent'

interface GroupFormationGraphProps {
  booking: BookingData
}

export function GroupFormationGraph({ booking }: GroupFormationGraphProps) {
  const statusColors = {
    pending: { bg: 'bg-gray-200', border: 'border-gray-400', text: 'text-gray-600' },
    accepted: { bg: 'bg-green-100', border: 'border-green-500', text: 'text-green-700' },
    declined: { bg: 'bg-red-100', border: 'border-red-500', text: 'text-red-700' },
    no_response: { bg: 'bg-yellow-100', border: 'border-yellow-500', text: 'text-yellow-700' },
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'accepted':
        return <Check className="w-4 h-4" />
      case 'declined':
        return <X className="w-4 h-4" />
      case 'pending':
      case 'no_response':
        return <Clock className="w-4 h-4" />
      default:
        return null
    }
  }

  const renderNode = (
    type: 'venue' | 'organizer' | 'invitee',
    name: string,
    status?: string,
    responseTime?: number
  ) => {
    if (type === 'venue') {
      return (
        <div className="flex flex-col items-center">
          <div className="w-20 h-20 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-full flex items-center justify-center shadow-lg">
            <MapPin className="w-10 h-10 text-white" />
          </div>
          <p className="mt-2 text-sm font-semibold text-gray-900 text-center max-w-[120px]">
            {name}
          </p>
          <p className="text-xs text-gray-500">Venue</p>
        </div>
      )
    }

    if (type === 'organizer') {
      return (
        <div className="flex flex-col items-center">
          <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-blue-600 rounded-full flex items-center justify-center shadow-md border-4 border-blue-300">
            <User className="w-8 h-8 text-white" />
          </div>
          <p className="mt-2 text-sm font-semibold text-gray-900">{name}</p>
          <p className="text-xs text-blue-600 font-medium">Organizer</p>
        </div>
      )
    }

    // Invitee
    const colors = status ? statusColors[status as keyof typeof statusColors] : statusColors.pending

    return (
      <div className="flex flex-col items-center">
        <div
          className={`w-14 h-14 ${colors.bg} rounded-full flex items-center justify-center shadow-sm border-3 ${colors.border} relative`}
        >
          <User className={`w-7 h-7 ${colors.text}`} />
          {status && status !== 'pending' && (
            <div
              className={`absolute -bottom-1 -right-1 w-6 h-6 rounded-full flex items-center justify-center ${
                status === 'accepted'
                  ? 'bg-green-500'
                  : status === 'declined'
                  ? 'bg-red-500'
                  : 'bg-yellow-500'
              } text-white`}
            >
              {getStatusIcon(status)}
            </div>
          )}
        </div>
        <p className="mt-2 text-xs font-medium text-gray-900">{name}</p>
        {status && (
          <p className={`text-xs ${colors.text} capitalize`}>{status.replace('_', ' ')}</p>
        )}
        {responseTime && (
          <p className="text-xs text-gray-400">{responseTime}s</p>
        )}
      </div>
    )
  }

  const renderConnection = (status?: string) => {
    let strokeStyle = 'stroke-gray-300 stroke-dasharray-none'
    
    if (status === 'accepted') {
      strokeStyle = 'stroke-green-500'
    } else if (status === 'declined') {
      strokeStyle = 'stroke-red-500'
    } else if (status === 'pending' || status === 'no_response') {
      strokeStyle = 'stroke-yellow-400 stroke-dasharray-[5,5]'
    }

    return strokeStyle
  }

  // Calculate positions
  const inviteeCount = booking.invitees.length
  const angleStep = inviteeCount > 0 ? (2 * Math.PI) / inviteeCount : 0

  return (
    <div className="bg-white rounded-xl p-8 shadow-sm border border-gray-100">
      <h3 className="text-lg font-semibold text-gray-900 mb-6">Group Formation</h3>

      {/* SVG Container */}
      <div className="relative w-full h-[500px] flex items-center justify-center">
        <svg className="absolute inset-0 w-full h-full" style={{ zIndex: 0 }}>
          {/* Draw connections from venue to organizer */}
          <line
            x1="50%"
            y1="50%"
            x2="50%"
            y2="30%"
            className={`stroke-2 ${renderConnection()}`}
          />

          {/* Draw connections from organizer to invitees */}
          {booking.invitees.map((invitee, idx) => {
            const angle = angleStep * idx - Math.PI / 2
            const x = 50 + Math.cos(angle) * 25
            const y = 30 + Math.sin(angle) * 25

            return (
              <line
                key={invitee.id}
                x1="50%"
                y1="30%"
                x2={`${x}%`}
                y2={`${y}%`}
                className={`stroke-2 ${renderConnection(invitee.status)}`}
              />
            )
          })}
        </svg>

        {/* Venue - Center */}
        <div className="absolute" style={{ top: '50%', left: '50%', transform: 'translate(-50%, -50%)' }}>
          {renderNode('venue', booking.venue_name)}
        </div>

        {/* Organizer - Top */}
        <div className="absolute" style={{ top: '30%', left: '50%', transform: 'translate(-50%, -50%)' }}>
          {renderNode('organizer', booking.organizer_name)}
        </div>

        {/* Invitees - Circle around */}
        {booking.invitees.map((invitee, idx) => {
          const angle = angleStep * idx - Math.PI / 2
          const x = 50 + Math.cos(angle) * 25
          const y = 30 + Math.sin(angle) * 25

          return (
            <div
              key={invitee.id}
              className="absolute"
              style={{
                top: `${y}%`,
                left: `${x}%`,
                transform: 'translate(-50%, -50%)',
              }}
            >
              {renderNode('invitee', invitee.username, invitee.status, invitee.response_time)}
            </div>
          )
        })}
      </div>

      {/* Legend */}
      <div className="mt-6 flex items-center justify-center gap-6 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-green-500" />
          <span className="text-gray-600">Accepted</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-yellow-400" />
          <span className="text-gray-600">Pending</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-red-500" />
          <span className="text-gray-600">Declined</span>
        </div>
      </div>

      {/* Status Summary */}
      <div className="mt-6 p-4 bg-gray-50 rounded-lg">
        <div className="grid grid-cols-4 gap-4 text-center">
          <div>
            <p className="text-2xl font-bold text-gray-900">{booking.invitees.length}</p>
            <p className="text-xs text-gray-500">Total Invited</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-green-600">
              {booking.invitees.filter((i) => i.status === 'accepted').length}
            </p>
            <p className="text-xs text-gray-500">Accepted</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-yellow-600">
              {booking.invitees.filter((i) => i.status === 'pending' || i.status === 'no_response').length}
            </p>
            <p className="text-xs text-gray-500">Pending</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-red-600">
              {booking.invitees.filter((i) => i.status === 'declined').length}
            </p>
            <p className="text-xs text-gray-500">Declined</p>
          </div>
        </div>
      </div>
    </div>
  )
}

