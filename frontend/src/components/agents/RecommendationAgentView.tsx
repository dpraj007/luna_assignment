/**
 * RecommendationAgentView - Visualize recommendation agent's reasoning and decisions
 */
import { useState, useEffect } from 'react'
import { Brain, MapPin, TrendingUp, Users, Sparkles, Star } from 'lucide-react'
import { UserSpectator } from './UserSpectator'
import { User, VenueRecommendation, SocialMatch, RecommendationContext } from '../../types/agent'
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  Tooltip,
} from 'recharts'

interface RecommendationAgentViewProps {
  events: any[]
}

export function RecommendationAgentView({ events }: RecommendationAgentViewProps) {
  const [users, setUsers] = useState<User[]>([])
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null)
  const [recommendations, setRecommendations] = useState<VenueRecommendation[]>([])
  const [socialMatches, setSocialMatches] = useState<SocialMatch[]>([])
  const [context, setContext] = useState<RecommendationContext | null>(null)
  const [explanations, setExplanations] = useState<string[]>([])
  const [loading, setLoading] = useState(true)

  // Fetch users on mount
  useEffect(() => {
    fetch('/api/v1/users')
      .then((res) => {
        if (!res.ok) {
          throw new Error(`Failed to fetch users: ${res.status}`)
        }
        return res.json()
      })
      .then((data) => {
        setUsers(data)
        if (data.length > 0 && !selectedUserId) {
          setSelectedUserId(data[0].id)
        }
      })
      .catch((error) => {
        console.error('Error fetching users:', error)
        setUsers([])
      })
      .finally(() => setLoading(false))
  }, [])

  // Fetch recommendations when user changes
  useEffect(() => {
    if (!selectedUserId) return

    setLoading(true)
    fetch(`/api/v1/recommendations/user/${selectedUserId}`)
      .then((res) => {
        if (!res.ok) {
          throw new Error(`Failed to fetch recommendations: ${res.status}`)
        }
        return res.json()
      })
      .then((data) => {
        setRecommendations(data.venues || [])
        setSocialMatches(data.people || [])
        setContext(data.context || null)
        setExplanations(data.explanations || [])
      })
      .catch((error) => {
        console.error('Error fetching recommendations:', error)
        setRecommendations([])
        setSocialMatches([])
        setContext(null)
        setExplanations([])
      })
      .finally(() => setLoading(false))
  }, [selectedUserId])

  // Listen for recommendation events
  useEffect(() => {
    const recommendationEvents = events.filter(
      (e) => e.event_type === 'recommendation_generated' && e.payload.user_id === selectedUserId
    )
    if (recommendationEvents.length > 0) {
      // Refetch recommendations
      if (selectedUserId) {
        fetch(`/api/v1/recommendations/user/${selectedUserId}`)
          .then((res) => {
            if (!res.ok) {
              throw new Error(`Failed to fetch recommendations: ${res.status}`)
            }
            return res.json()
          })
          .then((data) => {
            setRecommendations(data.venues || [])
            setSocialMatches(data.people || [])
            setContext(data.context || null)
            setExplanations(data.explanations || [])
          })
          .catch((error) => {
            console.error('Error fetching recommendations:', error)
          })
      }
    }
  }, [events, selectedUserId])

  const renderScoreBreakdown = (venue: VenueRecommendation) => {
    if (!venue.score_breakdown) return null

    const data = [
      { metric: 'Cuisine', value: venue.score_breakdown.cuisine_match * 100 },
      { metric: 'Distance', value: venue.score_breakdown.distance * 100 },
      { metric: 'Price', value: venue.score_breakdown.price_fit * 100 },
      { metric: 'Social', value: venue.score_breakdown.social_compatibility * 100 },
      { metric: 'Trending', value: venue.score_breakdown.trending_factor * 100 },
    ]

    return (
      <div className="mt-4">
        <p className="text-xs font-medium text-gray-700 mb-2">Compatibility Breakdown</p>
        <ResponsiveContainer width="100%" height={200}>
          <RadarChart data={data}>
            <PolarGrid stroke="#e5e7eb" />
            <PolarAngleAxis dataKey="metric" tick={{ fontSize: 10, fill: '#6b7280' }} />
            <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fontSize: 10 }} />
            <Radar dataKey="value" stroke="#6366f1" fill="#6366f1" fillOpacity={0.5} />
            <Tooltip />
          </RadarChart>
        </ResponsiveContainer>
      </div>
    )
  }

  const renderVenueCard = (venue: VenueRecommendation, index: number) => (
    <div
      key={venue.id}
      className={`bg-white rounded-xl p-5 border-2 transition-all hover:shadow-lg ${
        index === 0 ? 'border-indigo-300 shadow-md' : 'border-gray-200'
      }`}
    >
      {/* Rank Badge */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <span
            className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
              index === 0
                ? 'bg-gradient-to-br from-yellow-400 to-orange-500 text-white'
                : index === 1
                ? 'bg-gradient-to-br from-gray-300 to-gray-400 text-white'
                : index === 2
                ? 'bg-gradient-to-br from-orange-400 to-orange-600 text-white'
                : 'bg-gray-200 text-gray-600'
            }`}
          >
            {index + 1}
          </span>
          <div>
            <h4 className="font-semibold text-gray-900">{venue.name}</h4>
            <p className="text-sm text-gray-500">{venue.cuisine}</p>
          </div>
        </div>
        {venue.trending && (
          <span className="flex items-center gap-1 px-2 py-1 bg-red-100 text-red-700 text-xs font-medium rounded-full">
            <TrendingUp className="w-3 h-3" />
            Trending
          </span>
        )}
      </div>

      {/* Venue Details */}
      <div className="flex items-center gap-4 mb-3 text-sm text-gray-600">
        <div className="flex items-center gap-1">
          <span>{'$'.repeat(venue.price_level)}</span>
        </div>
        <div className="flex items-center gap-1">
          <MapPin className="w-4 h-4" />
          <span>{venue.distance_km?.toFixed(1)} km</span>
        </div>
        <div className="flex items-center gap-1">
          <Star className="w-4 h-4 fill-yellow-400 text-yellow-400" />
          <span>
            {venue.compatibility_score != null && !isNaN(venue.compatibility_score)
              ? (venue.compatibility_score * 100).toFixed(0)
              : venue.score != null && !isNaN(venue.score)
              ? (venue.score * 100).toFixed(0)
              : 'N/A'}%
          </span>
        </div>
      </div>

      {/* LLM Reasoning Highlight */}
      {venue.explanation && (
        <div className="mb-3 p-3 bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg border border-purple-200">
          <div className="flex items-start gap-2">
            <Sparkles className="w-4 h-4 text-purple-600 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-purple-900 italic">{venue.explanation}</p>
          </div>
        </div>
      )}

      {/* Score Breakdown */}
      {renderScoreBreakdown(venue)}
    </div>
  )

  const renderSocialMatch = (match: SocialMatch) => (
    <div
      key={match.id}
      className="bg-white rounded-lg p-4 border border-gray-200 hover:border-indigo-300 transition-all"
    >
      <div className="flex items-start justify-between mb-2">
        <div>
          <h5 className="font-semibold text-gray-900">{match.username}</h5>
          <div className="flex items-center gap-1 mt-1">
            <div className="w-full bg-gray-200 rounded-full h-2 max-w-[100px]">
              <div
                className="bg-gradient-to-r from-indigo-500 to-purple-500 h-2 rounded-full"
                style={{ 
                  width: `${match.compatibility_score != null && !isNaN(match.compatibility_score) 
                    ? match.compatibility_score * 100 
                    : 0}%` 
                }}
              />
            </div>
            <span className="text-xs font-medium text-gray-600">
              {match.compatibility_score != null && !isNaN(match.compatibility_score)
                ? (match.compatibility_score * 100).toFixed(0)
                : 'N/A'}%
            </span>
          </div>
        </div>
        {match.status && (
          <span className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded-full">
            {match.status}
          </span>
        )}
      </div>

      {/* LLM Social Reasoning */}
      {match.llm_reasoning && (
        <div className="mb-2 p-2 bg-gradient-to-r from-blue-50 to-purple-50 rounded border border-blue-200">
          <p className="text-xs text-blue-900 italic">{match.llm_reasoning}</p>
        </div>
      )}

      {/* Shared Interests */}
      {match.reasons && match.reasons.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {match.reasons.map((reason, idx) => (
            <span key={idx} className="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded-full">
              {reason}
            </span>
          ))}
        </div>
      )}
    </div>
  )

  if (loading && users.length === 0) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600" />
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
      {/* Left Sidebar - User Spectator */}
      <div className="lg:col-span-1">
        <UserSpectator
          users={users}
          selectedUserId={selectedUserId}
          onSelectUser={setSelectedUserId}
          context={context}
          currentActivity="Browsing venues"
        />
      </div>

      {/* Main Content */}
      <div className="lg:col-span-3 space-y-6">
        {/* Header */}
        <div className="bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl p-6 text-white">
          <div className="flex items-center gap-3 mb-2">
            <Brain className="w-8 h-8" />
            <h2 className="text-2xl font-bold">Recommendation Agent</h2>
          </div>
          <p className="text-indigo-100">
            Understanding why the AI recommends these venues and people
          </p>
        </div>

        {/* Explanations */}
        {explanations.length > 0 && (
          <div className="bg-gradient-to-r from-purple-100 to-indigo-100 rounded-xl p-5 border-2 border-purple-300">
            <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-purple-600" />
              AI Insights
            </h3>
            <div className="space-y-2">
              {explanations.map((exp, idx) => (
                <p key={idx} className="text-sm text-gray-800 italic">
                  • {exp}
                </p>
              ))}
            </div>
          </div>
        )}

        {/* Venue Recommendations */}
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Venue Recommendations</h3>
          {recommendations.length === 0 ? (
            <div className="bg-white rounded-xl p-8 text-center border border-gray-200">
              <MapPin className="w-12 h-12 text-gray-300 mx-auto mb-2" />
              <p className="text-gray-500">No recommendations yet</p>
              <p className="text-sm text-gray-400 mt-1">
                {selectedUserId
                  ? 'Recommendations will appear once generated'
                  : 'Select a user to view recommendations'}
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {recommendations.slice(0, 5).map((venue, idx) => renderVenueCard(venue, idx))}
            </div>
          )}
        </div>

        {/* Social Matches */}
        {socialMatches.length > 0 && (
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Users className="w-5 h-5" />
              Compatible Dining Partners
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {socialMatches.map(renderSocialMatch)}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

