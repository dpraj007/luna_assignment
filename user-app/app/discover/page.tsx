'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { Search, Filter, MapPin, DollarSign, X } from 'lucide-react'
import { api, Venue } from '@/lib/api-client'
import { formatDistance } from '@/lib/utils'
import { useUserStore } from '@/stores/userStore'
import { Navigation } from '@/components/shared/Navigation'

export default function DiscoverPage() {
  const [venues, setVenues] = useState<Venue[]>([])
  const [loading, setLoading] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedVenueDetail, setSelectedVenueDetail] = useState<Venue | null>(null)
  const [loadingVenueDetail, setLoadingVenueDetail] = useState(false)
  const [filterTrending, setFilterTrending] = useState(false)
  const [filterOpenNow, setFilterOpenNow] = useState(false)
  const { selectedVenueId, setSelectedVenue } = useUserStore()
  const searchQueryRef = useRef(searchQuery)

  // Keep searchQueryRef in sync with searchQuery
  useEffect(() => {
    searchQueryRef.current = searchQuery
  }, [searchQuery])

  const loadVenues = useCallback(async (query?: string) => {
    setLoading(true)
    try {
      const filters: {
        trending?: boolean
        open_now?: boolean
      } = {}
      
      if (filterTrending) {
        filters.trending = true
      }
      
      if (filterOpenNow) {
        filters.open_now = true
      }
      
      const searchTerm = query !== undefined ? query : searchQueryRef.current
      const results = await api.searchVenues(searchTerm, filters)
      setVenues(results)
    } catch (error) {
      console.error('Failed to load venues:', error)
    } finally {
      setLoading(false)
    }
  }, [filterTrending, filterOpenNow])

  // Reload venues when filters change
  useEffect(() => {
    loadVenues()
  }, [loadVenues])

  // Check for selectedVenueId and load venue details
  useEffect(() => {
    if (selectedVenueId) {
      loadVenueDetail(selectedVenueId)
    }
  }, [selectedVenueId])

  const loadVenueDetail = async (venueId: number) => {
    setLoadingVenueDetail(true)
    try {
      const venue = await api.getVenue(venueId)
      setSelectedVenueDetail(venue)
    } catch (error) {
      console.error('Failed to load venue details:', error)
      setSelectedVenueDetail(null)
      setSelectedVenue(null) // Clear selection on error
    } finally {
      setLoadingVenueDetail(false)
    }
  }

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    loadVenues(searchQueryRef.current)
  }

  const handleCloseVenueDetail = () => {
    setSelectedVenueDetail(null)
    setSelectedVenue(null)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-orange-50">
      <div className="container mx-auto px-4 py-6 max-w-6xl">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Discover Venues</h1>
          <p className="text-gray-600">Find your next dining adventure</p>
        </div>

        {/* Search Bar */}
        <form onSubmit={handleSearch} className="mb-6">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search for Italian food, outdoor seating, under $30..."
              className="w-full pl-12 pr-4 py-4 rounded-xl border-2 border-gray-200 focus:border-purple-500 focus:outline-none text-lg"
            />
            <button
              type="submit"
              className="absolute right-2 top-1/2 transform -translate-y-1/2 btn-primary py-2 px-6"
            >
              Search
            </button>
          </div>
        </form>

        {/* Filters */}
        <div className="flex items-center gap-4 mb-6">
          <button className="flex items-center gap-2 px-4 py-2 bg-white rounded-lg border border-gray-200 hover:border-purple-500 transition-colors">
            <Filter className="w-4 h-4" />
            <span>Filters</span>
          </button>
          <button 
            onClick={() => setFilterTrending(!filterTrending)}
            className={`px-4 py-2 rounded-lg border transition-colors text-sm ${
              filterTrending
                ? 'bg-purple-600 text-white border-purple-600'
                : 'bg-white text-gray-700 border-gray-200 hover:border-purple-500'
            }`}
          >
            Trending
          </button>
          <button 
            onClick={() => setFilterOpenNow(!filterOpenNow)}
            className={`px-4 py-2 rounded-lg border transition-colors text-sm ${
              filterOpenNow
                ? 'bg-purple-600 text-white border-purple-600'
                : 'bg-white text-gray-700 border-gray-200 hover:border-purple-500'
            }`}
          >
            Open Now
          </button>
        </div>

        {/* Results */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3, 4, 5, 6].map(i => (
              <div key={i} className="card h-64 animate-pulse bg-gray-200" />
            ))}
          </div>
        ) : venues.length === 0 ? (
          <div className="bg-white rounded-xl p-12 text-center">
            <p className="text-gray-500">No venues found. Try adjusting your search.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {venues.map((venue) => (
              <div
                key={venue.id}
                onClick={() => setSelectedVenue(venue.id)}
                className="card overflow-hidden cursor-pointer group"
              >
                <div className="relative h-48 bg-gradient-to-br from-purple-400 to-orange-400">
                  <div className="w-full h-full flex items-center justify-center text-white text-4xl font-bold">
                    {venue.name.charAt(0)}
                  </div>
                  {venue.trending && (
                    <div className="absolute top-2 right-2 badge-trending">
                      🔥 Trending
                    </div>
                  )}
                  {venue.availability && (
                    <div className="absolute bottom-2 left-2 bg-white/90 backdrop-blur-sm rounded-lg px-2 py-1">
                      <span className="text-xs font-semibold text-gray-900">
                        {venue.availability.available
                          ? `${venue.availability.slots_remaining} seats`
                          : 'Full'}
                      </span>
                    </div>
                  )}
                </div>
                <div className="p-4">
                  <h3 className="font-semibold text-lg text-gray-900 mb-1">{venue.name}</h3>
                  <p className="text-sm text-gray-600 mb-3">{venue.cuisine}</p>
                  <div className="flex items-center justify-between text-sm">
                    {venue.distance && (
                      <span className="flex items-center gap-1 text-gray-500">
                        <MapPin className="w-4 h-4" />
                        {formatDistance(venue.distance)}
                      </span>
                    )}
                    <span className="flex items-center gap-1 text-gray-500">
                      <DollarSign className="w-4 h-4" />
                      {venue.price_level}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Venue Detail Modal */}
      {selectedVenueDetail && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            {loadingVenueDetail ? (
              <div className="p-12 text-center">
                <div className="w-16 h-16 border-4 border-purple-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
                <p className="text-gray-600">Loading venue details...</p>
              </div>
            ) : (
              <>
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b">
                  <h2 className="text-2xl font-bold text-gray-900">Venue Details</h2>
                  <button
                    onClick={handleCloseVenueDetail}
                    className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>

                {/* Venue Info */}
                <div className="p-6">
                  <div className="mb-6">
                    <div className="relative h-64 bg-gradient-to-br from-purple-400 to-orange-400 rounded-xl mb-4">
                      <div className="w-full h-full flex items-center justify-center text-white text-6xl font-bold">
                        {selectedVenueDetail.name.charAt(0)}
                      </div>
                      {selectedVenueDetail.trending && (
                        <div className="absolute top-4 right-4 badge-trending">
                          🔥 Trending
                        </div>
                      )}
                    </div>
                    <h3 className="text-3xl font-bold text-gray-900 mb-2">{selectedVenueDetail.name}</h3>
                    <p className="text-lg text-gray-600 mb-4">{selectedVenueDetail.cuisine}</p>
                    
                    <div className="flex flex-wrap gap-4 text-sm text-gray-600 mb-6">
                      {selectedVenueDetail.rating && (
                        <span className="flex items-center gap-1">
                          ⭐ {selectedVenueDetail.rating.toFixed(1)}
                        </span>
                      )}
                      <span className="flex items-center gap-1">
                        <DollarSign className="w-4 h-4" />
                        {selectedVenueDetail.price_level}
                      </span>
                      {selectedVenueDetail.distance && (
                        <span className="flex items-center gap-1">
                          <MapPin className="w-4 h-4" />
                          {formatDistance(selectedVenueDetail.distance)}
                        </span>
                      )}
                    </div>

                    {selectedVenueDetail.availability && (
                      <div className="bg-gray-50 rounded-lg p-4 mb-6">
                        <p className="font-semibold text-gray-900 mb-1">Availability</p>
                        <p className="text-sm text-gray-600">
                          {selectedVenueDetail.availability.available
                            ? `${selectedVenueDetail.availability.slots_remaining} seats available`
                            : 'Currently full'}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      <Navigation />
    </div>
  )
}

