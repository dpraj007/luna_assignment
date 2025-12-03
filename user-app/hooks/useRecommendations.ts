import { useEffect, useState } from 'react'
import { api, Recommendation } from '@/lib/api-client'
import { useUserStore } from '@/stores/userStore'

// Transform API venue response to Recommendation format
function transformVenueToRecommendation(v: any): Recommendation {
  return {
    venue: {
      id: v.id,
      name: v.name,
      cuisine: v.cuisine_type || v.category || 'Restaurant',
      address: v.address,
      city: v.city,
      latitude: v.latitude,
      longitude: v.longitude,
      price_level: v.price_level || 2,
      rating: v.rating,
      ambiance: v.ambiance || [],
      image_url: v.image_url,
      trending: v.trending || false,
      distance: v.distance_km,
    },
    score: v.score || 0,
    match_score: Math.round((v.score || 0) * 100),
    reasons: [],
    reasoning: v.reasoning,
    gnn_score: v.gnn_score,
    rule_score: v.rule_score,
  }
}

export function useRecommendations(userId: number | null) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { recommendations, setRecommendations } = useUserStore()

  useEffect(() => {
    if (!userId) return

    const fetchRecommendations = async () => {
      setLoading(true)
      setError(null)
      try {
        const data = await api.getRecommendations(userId)
        // Transform API response to Recommendation format
        if (data && Array.isArray(data.venues)) {
          const transformed = data.venues.map(transformVenueToRecommendation)
          setRecommendations(transformed)
        }
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to load recommendations'
        setError(errorMessage)
        console.error('Failed to fetch recommendations:', err)
        // Don't clear existing recommendations on error - keep what we have
      } finally {
        setLoading(false)
      }
    }

    fetchRecommendations()
    
    // Refresh every 30 seconds
    const interval = setInterval(fetchRecommendations, 30000)
    return () => clearInterval(interval)
  }, [userId, setRecommendations])

  return { recommendations, loading, error, refetch: () => {
    if (userId) {
      api.getRecommendations(userId)
        .then(data => {
          if (data && Array.isArray(data.venues)) {
            const transformed = data.venues.map(transformVenueToRecommendation)
            setRecommendations(transformed)
          }
        })
        .catch(err => {
          console.error('Failed to refetch recommendations:', err)
          // Don't clear existing recommendations on error
        })
    }
  } }
}

