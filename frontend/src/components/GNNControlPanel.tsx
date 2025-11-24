/**
 * GNN Control Panel - Manages GNN model training and displays status.
 */
import { useState, useEffect } from 'react'
import { Brain, Play, Loader2, CheckCircle, XCircle, AlertCircle } from 'lucide-react'

interface GNNStatus {
  model_available: boolean
  num_users?: number
  num_venues?: number
  num_edges?: number
  model_path?: string
  message?: string
  error?: string
}

interface TrainingMetrics {
  num_users: number
  num_venues: number
  num_edges: number
  epochs: number
  final_loss: number
  best_loss: number
  losses: number[]
  model_path: string
}

interface TrainingRequest {
  min_interactions?: number
  include_friendships?: boolean
  embedding_dim?: number
  num_layers?: number
  learning_rate?: number
  batch_size?: number
  epochs?: number
}

const API_BASE = '/api/v1'

export function GNNControlPanel() {
  const [status, setStatus] = useState<GNNStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [training, setTraining] = useState(false)
  const [trainingMetrics, setTrainingMetrics] = useState<TrainingMetrics | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [trainingParams, setTrainingParams] = useState<TrainingRequest>({
    min_interactions: 1,
    include_friendships: true,
    embedding_dim: 64,
    num_layers: 3,
    learning_rate: 0.001,
    batch_size: 2048,
    epochs: 100,
  })

  const fetchStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/admin/gnn/status`)
      if (response.ok) {
        const data = await response.json()
        setStatus(data)
        setError(null)
      } else {
        setError('Failed to fetch GNN status')
      }
    } catch (e) {
      console.error('Failed to fetch GNN status:', e)
      setError('Failed to connect to server')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStatus()
    // Poll status every 30 seconds
    const interval = setInterval(fetchStatus, 30000)
    return () => clearInterval(interval)
  }, [])

  const handleTrain = async () => {
    setTraining(true)
    setError(null)
    setTrainingMetrics(null)

    try {
      const response = await fetch(`${API_BASE}/admin/gnn/train`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(trainingParams),
      })

      const data = await response.json()

      if (data.success) {
        setTrainingMetrics(data.metrics)
        // Refresh status after training
        await fetchStatus()
      } else {
        setError(data.error || 'Training failed')
      }
    } catch (e) {
      console.error('Training error:', e)
      setError('Failed to start training. Check server connection.')
    } finally {
      setTraining(false)
    }
  }

  if (loading) {
    return (
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4" />
          <div className="h-20 bg-gray-200 rounded" />
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Brain className="w-5 h-5 text-indigo-600" />
          <h3 className="text-lg font-semibold text-gray-900">GNN Model</h3>
        </div>
        {status?.model_available ? (
          <div className="flex items-center gap-2 text-green-600">
            <CheckCircle className="w-4 h-4" />
            <span className="text-sm font-medium">Available</span>
          </div>
        ) : (
          <div className="flex items-center gap-2 text-gray-400">
            <XCircle className="w-4 h-4" />
            <span className="text-sm font-medium">Not Trained</span>
          </div>
        )}
      </div>

      {/* Status Display */}
      {status?.model_available && (
        <div className="mb-4 p-4 bg-green-50 rounded-lg border border-green-200">
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <p className="text-gray-500">Users</p>
              <p className="font-semibold text-gray-900">{status.num_users || 0}</p>
            </div>
            <div>
              <p className="text-gray-500">Venues</p>
              <p className="font-semibold text-gray-900">{status.num_venues || 0}</p>
            </div>
            <div>
              <p className="text-gray-500">Edges</p>
              <p className="font-semibold text-gray-900">{status.num_edges || 0}</p>
            </div>
          </div>
        </div>
      )}

      {/* Training Metrics */}
      {trainingMetrics && (
        <div className="mb-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
          <p className="text-sm font-semibold text-blue-900 mb-2">Last Training Results</p>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <span className="text-blue-700">Final Loss:</span>{' '}
              <span className="font-semibold">{trainingMetrics.final_loss.toFixed(4)}</span>
            </div>
            <div>
              <span className="text-blue-700">Best Loss:</span>{' '}
              <span className="font-semibold">{trainingMetrics.best_loss.toFixed(4)}</span>
            </div>
            <div>
              <span className="text-blue-700">Epochs:</span>{' '}
              <span className="font-semibold">{trainingMetrics.epochs}</span>
            </div>
            <div>
              <span className="text-blue-700">Model:</span>{' '}
              <span className="font-semibold text-xs truncate">{trainingMetrics.model_path.split('/').pop()}</span>
            </div>
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 rounded-lg border border-red-200 flex items-start gap-2">
          <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0 mt-0.5" />
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {/* Training Controls */}
      <div className="space-y-4">
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="text-sm text-indigo-600 hover:text-indigo-700 font-medium"
        >
          {showAdvanced ? 'Hide' : 'Show'} Advanced Options
        </button>

        {showAdvanced && (
          <div className="space-y-3 p-4 bg-gray-50 rounded-lg">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-gray-600 mb-1 block">Min Interactions</label>
                <input
                  type="number"
                  value={trainingParams.min_interactions}
                  onChange={(e) =>
                    setTrainingParams({ ...trainingParams, min_interactions: parseInt(e.target.value) || 1 })
                  }
                  className="w-full px-2 py-1 text-sm border border-gray-300 rounded"
                  min="1"
                />
              </div>
              <div>
                <label className="text-xs text-gray-600 mb-1 block">Epochs</label>
                <input
                  type="number"
                  value={trainingParams.epochs}
                  onChange={(e) =>
                    setTrainingParams({ ...trainingParams, epochs: parseInt(e.target.value) || 100 })
                  }
                  className="w-full px-2 py-1 text-sm border border-gray-300 rounded"
                  min="1"
                />
              </div>
              <div>
                <label className="text-xs text-gray-600 mb-1 block">Embedding Dim</label>
                <input
                  type="number"
                  value={trainingParams.embedding_dim}
                  onChange={(e) =>
                    setTrainingParams({ ...trainingParams, embedding_dim: parseInt(e.target.value) || 64 })
                  }
                  className="w-full px-2 py-1 text-sm border border-gray-300 rounded"
                  min="16"
                />
              </div>
              <div>
                <label className="text-xs text-gray-600 mb-1 block">Num Layers</label>
                <input
                  type="number"
                  value={trainingParams.num_layers}
                  onChange={(e) =>
                    setTrainingParams({ ...trainingParams, num_layers: parseInt(e.target.value) || 3 })
                  }
                  className="w-full px-2 py-1 text-sm border border-gray-300 rounded"
                  min="1"
                  max="5"
                />
              </div>
              <div>
                <label className="text-xs text-gray-600 mb-1 block">Learning Rate</label>
                <input
                  type="number"
                  step="0.0001"
                  value={trainingParams.learning_rate}
                  onChange={(e) =>
                    setTrainingParams({ ...trainingParams, learning_rate: parseFloat(e.target.value) || 0.001 })
                  }
                  className="w-full px-2 py-1 text-sm border border-gray-300 rounded"
                  min="0.0001"
                />
              </div>
              <div>
                <label className="text-xs text-gray-600 mb-1 block">Batch Size</label>
                <input
                  type="number"
                  value={trainingParams.batch_size}
                  onChange={(e) =>
                    setTrainingParams({ ...trainingParams, batch_size: parseInt(e.target.value) || 2048 })
                  }
                  className="w-full px-2 py-1 text-sm border border-gray-300 rounded"
                  min="256"
                />
              </div>
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="include_friendships"
                checked={trainingParams.include_friendships}
                onChange={(e) =>
                  setTrainingParams({ ...trainingParams, include_friendships: e.target.checked })
                }
                className="w-4 h-4"
              />
              <label htmlFor="include_friendships" className="text-sm text-gray-700">
                Include Friendships
              </label>
            </div>
          </div>
        )}

        <button
          onClick={handleTrain}
          disabled={training}
          className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {training ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Training...</span>
            </>
          ) : (
            <>
              <Play className="w-4 h-4" />
              <span>Train Model</span>
            </>
          )}
        </button>
      </div>

      {status?.message && !status.model_available && (
        <p className="mt-4 text-xs text-gray-500 text-center">{status.message}</p>
      )}
    </div>
  )
}

export default GNNControlPanel

