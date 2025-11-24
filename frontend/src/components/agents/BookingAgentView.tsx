/**
 * BookingAgentView - Visualize booking agent's coordination and group formation
 */
import { useState, useEffect, useRef } from 'react'
import {
  Calendar,
  CheckCircle,
  XCircle,
  Clock,
  AlertCircle,
  ChevronRight,
  Users,
} from 'lucide-react'
import { GroupFormationGraph } from './GroupFormationGraph'
import { BookingData, BookingStep, BookingError, DecisionLogEntry } from '../../types/agent'

interface BookingAgentViewProps {
  events: any[]
}

export function BookingAgentView({ events }: BookingAgentViewProps) {
  const [activeBookings, setActiveBookings] = useState<BookingData[]>([])
  const [selectedBookingId, setSelectedBookingId] = useState<number | null>(null)
  const [bookingErrors] = useState<BookingError[]>([])
  const [loading, setLoading] = useState(true)

  // Track the last processed booking event count to avoid unnecessary re-renders
  const lastBookingEventCountRef = useRef<number>(0)
  const debounceTimerRef = useRef<number | null>(null)

  // Fetch active bookings on mount
  useEffect(() => {
    fetchActiveBookings()
  }, [])

  // Listen for booking events with debouncing to prevent excessive re-renders
  // Only react when the count of booking events changes, not the entire events array
  useEffect(() => {
    // Count booking-related events
    const bookingEventCount = events.filter(
      (e) =>
        e.event_type === 'booking_created' ||
        e.event_type === 'booking_confirmed' ||
        e.event_type === 'invite_sent' ||
        e.event_type === 'invite_response'
    ).length

    // Only proceed if we have new booking events
    if (bookingEventCount > lastBookingEventCountRef.current && bookingEventCount > 0) {
      lastBookingEventCountRef.current = bookingEventCount

      // Clear existing timer
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current)
      }

      // Set new timer to fetch after 2 seconds of no new events
      debounceTimerRef.current = setTimeout(() => {
        fetchActiveBookings()
      }, 2000)
    }

    // Cleanup on unmount
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current)
      }
    }
  }, [events.length]) // Only depend on events.length, not the entire array

  const fetchActiveBookings = async () => {
    setLoading(true)
    try {
      const res = await fetch('/api/v1/bookings?limit=50')
      const data = await res.json()

      // Transform the data to match our BookingData interface
      const transformedBookings: BookingData[] = data.map((booking: any) => ({
        id: booking.id,
        organizer_id: booking.user_id,
        organizer_name: booking.user?.username || `User ${booking.user_id}`,
        venue_id: booking.venue_id,
        venue_name: booking.venue?.name || `Venue ${booking.venue_id}`,
        party_size: booking.party_size,
        requested_party_size: booking.party_size,
        booking_time: booking.booking_time,
        confirmation_code: booking.confirmation_code,
        status: booking.status,
        steps: generateStepsFromStatus(booking.status),
        invitees: booking.invitations?.map((inv: any) => ({
          id: inv.invitee_id,
          username: inv.invitee?.username || `User ${inv.invitee_id}`,
          status: inv.status,
          response_time: inv.responded_at
            ? Math.floor(
              (new Date(inv.responded_at).getTime() - new Date(inv.created_at).getTime()) / 1000
            )
            : undefined,
        })) || [],
        decision_log: generateDecisionLog(booking),
        created_at: booking.created_at,
      }))

      // Debug: Log the first booking to check timestamp format
      if (transformedBookings.length > 0) {
        console.log('Sample booking data:', {
          created_at: data[0]?.created_at,
          updated_at: data[0]?.updated_at,
          booking_time: data[0]?.booking_time,
          decision_log_sample: transformedBookings[0].decision_log[0]
        })
      }

      setActiveBookings(transformedBookings)

      // Preserve selected booking if it still exists, otherwise select first one
      if (transformedBookings.length > 0) {
        const selectedStillExists = transformedBookings.some(b => b.id === selectedBookingId)
        if (!selectedBookingId || !selectedStillExists) {
          setSelectedBookingId(transformedBookings[0].id)
        }
      }
    } catch (error) {
      console.error('Failed to fetch bookings:', error)
    } finally {
      setLoading(false)
    }
  }

  const generateStepsFromStatus = (status: string): BookingStep[] => {
    const steps: BookingStep[] = [
      { name: 'Validate Venue', status: 'completed', details: 'Venue availability confirmed' },
      { name: 'Find Optimal Time', status: 'completed', details: 'Time slot selected' },
      { name: 'Send Invitations', status: 'completed', details: 'Invitations sent' },
      { name: 'Await Responses', status: 'active', details: 'Waiting for RSVPs' },
      { name: 'Confirm Booking', status: 'pending' },
    ]

    if (status === 'confirmed') {
      steps[3].status = 'completed'
      steps[4].status = 'completed'
      steps[4].details = 'Booking confirmed successfully'
    } else if (status === 'failed') {
      steps.forEach((s) => {
        if (s.status === 'active' || s.status === 'pending') {
          s.status = 'failed'
        }
      })
    }

    return steps
  }

  const generateDecisionLog = (booking: any): DecisionLogEntry[] => {
    const log: DecisionLogEntry[] = []

    log.push({
      timestamp: booking.created_at,
      message: `Booking initiated by ${booking.user?.username || `User ${booking.user_id}`}`,
      type: 'info',
    })

    log.push({
      timestamp: booking.created_at,
      message: `Venue validated: ${booking.venue?.name || `Venue ${booking.venue_id}`}`,
      type: 'success',
    })

    log.push({
      timestamp: booking.created_at,
      message: `Optimal time selected: ${new Date(booking.booking_time).toLocaleString()}`,
      type: 'success',
    })

    if (booking.invitations && booking.invitations.length > 0) {
      log.push({
        timestamp: booking.created_at,
        message: `${booking.invitations.length} invitations sent via agent`,
        type: 'info',
      })

      booking.invitations.forEach((inv: any) => {
        if (inv.responded_at) {
          log.push({
            timestamp: inv.responded_at,
            message: `${inv.invitee?.username || `User ${inv.invitee_id}`} ${inv.status === 'accepted' ? 'accepted' : 'declined'
              }`,
            type: inv.status === 'accepted' ? 'success' : 'warning',
          })
        }
      })
    }

    if (booking.status === 'confirmed') {
      log.push({
        timestamp: booking.updated_at || booking.created_at,
        message: `Booking confirmed - Code: ${booking.confirmation_code}`,
        type: 'success',
      })
    }

    return log
  }

  const selectedBooking = activeBookings.find((b) => b.id === selectedBookingId)

  const getStepIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-600" />
      case 'active':
        return <Clock className="w-5 h-5 text-blue-600" />
      case 'waiting':
        return <Clock className="w-5 h-5 text-yellow-600" />
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-600" />
      default:
        return <div className="w-5 h-5 rounded-full border-2 border-gray-300" />
    }
  }

  const renderBookingListItem = (booking: BookingData) => {
    const statusColors = {
      initiated: 'bg-blue-100 text-blue-700 border-blue-300',
      pending: 'bg-yellow-100 text-yellow-700 border-yellow-300',
      confirmed: 'bg-green-100 text-green-700 border-green-300',
      failed: 'bg-red-100 text-red-700 border-red-300',
    }

    // Safely parse the created_at timestamp
    const createdDate = booking.created_at ? new Date(booking.created_at) : null
    const isValidDate = createdDate && !isNaN(createdDate.getTime())
    const timeString = isValidDate ? createdDate.toLocaleTimeString() : 'N/A'

    return (
      <button
        key={booking.id}
        onClick={() => setSelectedBookingId(booking.id)}
        className={`w-full text-left p-4 rounded-lg border-2 transition-all ${selectedBookingId === booking.id
          ? 'border-indigo-500 bg-indigo-50'
          : 'border-gray-200 bg-white hover:border-gray-300'
          }`}
      >
        <div className="flex items-start justify-between mb-2">
          <div className="flex-1">
            <p className="font-semibold text-gray-900 text-sm">{booking.venue_name}</p>
            <p className="text-xs text-gray-500">by {booking.organizer_name}</p>
          </div>
          <span
            className={`px-2 py-1 rounded-full text-xs font-medium border ${statusColors[booking.status as keyof typeof statusColors]
              }`}
          >
            {booking.status}
          </span>
        </div>
        <div className="flex items-center gap-3 text-xs text-gray-600">
          <span className="flex items-center gap-1">
            <Users className="w-3 h-3" />
            {booking.party_size}
          </span>
          <span className="flex items-center gap-1">
            <Calendar className="w-3 h-3" />
            {timeString}
          </span>
        </div>
      </button>
    )
  }

  const renderPipelineStepper = () => {
    if (!selectedBooking) return null

    return (
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <h3 className="text-lg font-semibold text-gray-900 mb-6">Booking Pipeline</h3>
        <div className="space-y-4">
          {selectedBooking.steps.map((step, idx) => (
            <div key={idx} className="flex items-start gap-4">
              <div className="flex-shrink-0 mt-1">{getStepIcon(step.status)}</div>
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <h4
                    className={`font-medium ${step.status === 'completed'
                      ? 'text-green-700'
                      : step.status === 'active'
                        ? 'text-blue-700'
                        : step.status === 'failed'
                          ? 'text-red-700'
                          : 'text-gray-500'
                      }`}
                  >
                    {step.name}
                  </h4>
                  {step.duration && (
                    <span className="text-xs text-gray-400">{step.duration}ms</span>
                  )}
                </div>
                {step.details && <p className="text-sm text-gray-600 mt-1">{step.details}</p>}
              </div>
              {idx < selectedBooking.steps.length - 1 && (
                <ChevronRight className="w-5 h-5 text-gray-300 flex-shrink-0 mt-1" />
              )}
            </div>
          ))}
        </div>
      </div>
    )
  }

  const renderDecisionLog = () => {
    if (!selectedBooking) return null

    const typeColors = {
      info: 'bg-blue-50 border-blue-200 text-blue-800',
      success: 'bg-green-50 border-green-200 text-green-800',
      warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
      error: 'bg-red-50 border-red-200 text-red-800',
    }

    return (
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Decision Log</h3>
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {selectedBooking.decision_log.map((entry, idx) => {
            // Safely parse the timestamp
            const timestamp = entry.timestamp ? new Date(entry.timestamp) : null
            const isValidDate = timestamp && !isNaN(timestamp.getTime())
            const timeString = isValidDate
              ? timestamp.toLocaleTimeString()
              : 'N/A'

            return (
              <div
                key={idx}
                className={`p-3 rounded-lg border ${typeColors[entry.type || 'info']
                  }`}
              >
                <div className="flex justify-between items-start">
                  <p className="text-sm">{entry.message}</p>
                  <span className="text-xs whitespace-nowrap ml-2 opacity-75">
                    {timeString}
                  </span>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    )
  }

  const renderStats = () => {
    const total = activeBookings.length
    const confirmed = activeBookings.filter((b) => b.status === 'confirmed').length
    const pending = activeBookings.filter((b) => b.status === 'pending' || b.status === 'initiated').length
    const successRate = total > 0 ? ((confirmed / total) * 100).toFixed(0) : 0

    return (
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-lg p-4 border border-gray-200">
          <p className="text-sm text-gray-500">Total Bookings</p>
          <p className="text-2xl font-bold text-gray-900">{total}</p>
        </div>
        <div className="bg-green-50 rounded-lg p-4 border border-green-200">
          <p className="text-sm text-green-600">Confirmed</p>
          <p className="text-2xl font-bold text-green-700">{confirmed}</p>
        </div>
        <div className="bg-yellow-50 rounded-lg p-4 border border-yellow-200">
          <p className="text-sm text-yellow-600">Pending</p>
          <p className="text-2xl font-bold text-yellow-700">{pending}</p>
        </div>
        <div className="bg-indigo-50 rounded-lg p-4 border border-indigo-200">
          <p className="text-sm text-indigo-600">Success Rate</p>
          <p className="text-2xl font-bold text-indigo-700">{successRate}%</p>
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-green-500 to-teal-600 rounded-xl p-6 text-white">
        <div className="flex items-center gap-3 mb-2">
          <Calendar className="w-8 h-8" />
          <h2 className="text-2xl font-bold">Booking Agent</h2>
        </div>
        <p className="text-green-100">
          Coordinating group formations and automated reservations
        </p>
      </div>

      {/* Stats */}
      {renderStats()}

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Left Sidebar - Booking List */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100 sticky top-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Active Bookings</h3>
            <div className="space-y-2 max-h-[600px] overflow-y-auto">
              {activeBookings.length === 0 ? (
                <div className="text-center py-8">
                  <Calendar className="w-12 h-12 text-gray-300 mx-auto mb-2" />
                  <p className="text-sm text-gray-400">No active bookings</p>
                </div>
              ) : (
                activeBookings.map(renderBookingListItem)
              )}
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="lg:col-span-3 space-y-6">
          {selectedBooking ? (
            <>
              {/* Booking Details */}
              <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-xl font-semibold text-gray-900">
                      {selectedBooking.venue_name}
                    </h3>
                    <p className="text-gray-500">
                      Organized by {selectedBooking.organizer_name}
                    </p>
                  </div>
                  {selectedBooking.confirmation_code && (
                    <div className="text-right">
                      <p className="text-xs text-gray-500">Confirmation Code</p>
                      <p className="text-lg font-mono font-bold text-indigo-600">
                        {selectedBooking.confirmation_code}
                      </p>
                    </div>
                  )}
                </div>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <p className="text-gray-500">Party Size</p>
                    <p className="font-semibold text-gray-900">{selectedBooking.party_size} people</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Booking Time</p>
                    <p className="font-semibold text-gray-900">
                      {new Date(selectedBooking.booking_time).toLocaleString()}
                    </p>
                  </div>
                  <div>
                    <p className="text-gray-500">Status</p>
                    <p className="font-semibold text-gray-900 capitalize">{selectedBooking.status}</p>
                  </div>
                </div>
              </div>

              {/* Pipeline Stepper */}
              {renderPipelineStepper()}

              {/* Group Formation Graph */}
              {selectedBooking.invitees.length > 0 && (
                <GroupFormationGraph booking={selectedBooking} />
              )}

              {/* Decision Log */}
              {renderDecisionLog()}
            </>
          ) : (
            <div className="bg-white rounded-xl p-12 text-center border border-gray-200">
              <AlertCircle className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">Select a booking to view details</p>
            </div>
          )}
        </div>
      </div>

      {/* Error Log */}
      {bookingErrors.length > 0 && (
        <div className="bg-white rounded-xl p-6 shadow-sm border border-red-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-red-600" />
            Failed Bookings
          </h3>
          <div className="space-y-2">
            {bookingErrors.map((error, idx) => (
              <div key={idx} className="p-4 bg-red-50 rounded-lg border border-red-200">
                <div className="flex justify-between items-start mb-2">
                  <p className="font-medium text-red-900">{error.venue_name}</p>
                  <span className="text-xs text-red-600">
                    {new Date(error.timestamp).toLocaleString()}
                  </span>
                </div>
                <p className="text-sm text-red-700">Reason: {error.reason}</p>
                {error.agent_decision && (
                  <p className="text-sm text-red-600 mt-1">Agent: {error.agent_decision}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

