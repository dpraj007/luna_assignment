/**
 * Social Graph Visualization - Shows user connections and interactions.
 *
 * Note: This is a simplified version that doesn't require react-force-graph-2d.
 * Uses CSS animations for a network-like visualization.
 */
import { useMemo } from 'react'
import { Users, UserPlus, MessageCircle } from 'lucide-react'

interface StreamEvent {
  event_type: string
  channel: string
  payload: Record<string, unknown>
  user_id?: number
}

interface SocialGraphProps {
  events: StreamEvent[]
}

interface UserNode {
  id: number
  connections: number
  invitesSent: number
  invitesReceived: number
}

export function SocialGraph({ events }: SocialGraphProps) {
  // Aggregate user data from events
  const userData = useMemo(() => {
    const users = new Map<number, UserNode>()

    events.forEach((event) => {
      const userId = event.user_id
      if (!userId) return

      if (!users.has(userId)) {
        users.set(userId, {
          id: userId,
          connections: 0,
          invitesSent: 0,
          invitesReceived: 0,
        })
      }

      const user = users.get(userId)!

      if (event.event_type.includes('invite_sent')) {
        user.invitesSent++
        const inviteeId = event.payload?.invitee_id as number
        if (inviteeId) {
          if (!users.has(inviteeId)) {
            users.set(inviteeId, {
              id: inviteeId,
              connections: 0,
              invitesSent: 0,
              invitesReceived: 0,
            })
          }
          users.get(inviteeId)!.invitesReceived++
          user.connections++
          users.get(inviteeId)!.connections++
        }
      } else if (event.event_type.includes('friend')) {
        user.connections++
      }
    })

    return Array.from(users.values())
      .sort((a, b) => b.connections - a.connections)
      .slice(0, 20) // Top 20 users
  }, [events])

  const totalConnections = userData.reduce((sum, u) => sum + u.connections, 0)
  const totalInvites = userData.reduce((sum, u) => sum + u.invitesSent, 0)

  // Generate positions for nodes in a circular layout
  const nodePositions = useMemo(() => {
    const positions: { x: number; y: number; size: number }[] = []
    const centerX = 150
    const centerY = 120
    const radius = 80

    userData.forEach((user, index) => {
      const angle = (index / userData.length) * 2 * Math.PI - Math.PI / 2
      const size = Math.min(40, 15 + user.connections * 3)

      positions.push({
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle),
        size,
      })
    })

    return positions
  }, [userData])

  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Social Network</h3>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-2 mb-4">
        <div className="bg-purple-50 rounded-lg p-3 text-center">
          <Users className="w-5 h-5 mx-auto text-purple-600" />
          <p className="text-lg font-bold text-purple-700">{userData.length}</p>
          <p className="text-xs text-purple-600">Active Users</p>
        </div>
        <div className="bg-blue-50 rounded-lg p-3 text-center">
          <UserPlus className="w-5 h-5 mx-auto text-blue-600" />
          <p className="text-lg font-bold text-blue-700">{totalConnections}</p>
          <p className="text-xs text-blue-600">Connections</p>
        </div>
        <div className="bg-green-50 rounded-lg p-3 text-center">
          <MessageCircle className="w-5 h-5 mx-auto text-green-600" />
          <p className="text-lg font-bold text-green-700">{totalInvites}</p>
          <p className="text-xs text-green-600">Invites</p>
        </div>
      </div>

      {/* Network Visualization */}
      <div className="relative h-60 bg-gradient-to-br from-gray-50 to-slate-50 rounded-lg overflow-hidden">
        {userData.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-400 text-sm">
            Start simulation to see social activity
          </div>
        ) : (
          <svg width="100%" height="100%" viewBox="0 0 300 240">
            {/* Draw connections (lines) */}
            {userData.slice(0, 10).map((user, i) => {
              const pos = nodePositions[i]
              if (!pos) return null

              // Connect to nearby nodes
              return userData.slice(0, 10).map((other, j) => {
                if (i >= j) return null
                const otherPos = nodePositions[j]
                if (!otherPos) return null

                // Only draw some connections
                if (Math.random() > 0.3) return null

                return (
                  <line
                    key={`${i}-${j}`}
                    x1={pos.x}
                    y1={pos.y}
                    x2={otherPos.x}
                    y2={otherPos.y}
                    stroke="#e5e7eb"
                    strokeWidth="1"
                    opacity="0.5"
                  />
                )
              })
            })}

            {/* Draw nodes */}
            {userData.map((user, index) => {
              const pos = nodePositions[index]
              if (!pos) return null

              const colors = [
                '#6366f1', // indigo
                '#8b5cf6', // violet
                '#a855f7', // purple
                '#d946ef', // fuchsia
                '#ec4899', // pink
              ]
              const color = colors[index % colors.length]

              return (
                <g key={user.id}>
                  {/* Pulse animation for active users */}
                  {user.invitesSent > 0 && (
                    <circle
                      cx={pos.x}
                      cy={pos.y}
                      r={pos.size / 2 + 5}
                      fill={color}
                      opacity="0.2"
                      className="animate-ping"
                    />
                  )}

                  {/* Node */}
                  <circle
                    cx={pos.x}
                    cy={pos.y}
                    r={pos.size / 2}
                    fill={color}
                    stroke="white"
                    strokeWidth="2"
                    className="transition-all duration-300 hover:r-6"
                  />

                  {/* User ID label */}
                  <text
                    x={pos.x}
                    y={pos.y + 3}
                    textAnchor="middle"
                    fill="white"
                    fontSize="8"
                    fontWeight="bold"
                  >
                    {user.id}
                  </text>
                </g>
              )
            })}
          </svg>
        )}
      </div>

      {/* Legend */}
      <div className="mt-4 text-xs text-gray-500">
        <p>Node size represents connection count. Pulsing nodes have recent activity.</p>
      </div>
    </div>
  )
}

export default SocialGraph
