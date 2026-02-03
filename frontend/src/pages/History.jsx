import React, { useState, useEffect } from 'react'
import { s3Api } from '../services/api'
import EnhancedRecommendationTable from '../components/EnhancedRecommendationTable'

const History = () => {
  const [availableDates, setAvailableDates] = useState([])
  const [selectedDate, setSelectedDate] = useState('')
  const [historicalData, setHistoricalData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchAvailableDates()
  }, [])

  const fetchAvailableDates = async () => {
    try {
      setLoading(true)
      setError(null)
      
      // Get real dates from API
      const response = await s3Api.listAvailableDates()
      const dates = response.dates || []
      
      setAvailableDates(dates)
      if (dates.length > 0) {
        setSelectedDate(dates[0]) // Select the most recent date
      }
    } catch (err) {
      setError('Failed to fetch available dates')
      console.error('Error fetching dates:', err)
    } finally {
      setLoading(false)
    }
  }

  const fetchHistoricalData = async (date) => {
    if (!date) return
    
    try {
      setLoading(true)
      setError(null)
      // Use enhanced endpoint to get reconciliation data
      const data = await s3Api.getHistoricalRecommendationsEnhanced(date)
      setHistoricalData(data)
    } catch (err) {
      setError(err.message)
      setHistoricalData(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (selectedDate) {
      fetchHistoricalData(selectedDate)
    }
  }, [selectedDate])

  const formatDate = (dateString) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Historical Recommendations</h1>
        <p className="mt-2 text-gray-600">
          View past stock recommendations and track performance over time
        </p>
      </div>

      {/* Date Selector */}
      <div className="card mb-8">
        <div className="flex items-center space-x-4">
          <div className="flex-1">
            <label htmlFor="date-select" className="block text-sm font-medium text-gray-700 mb-2">
              Select Date
            </label>
            <select
              id="date-select"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              disabled={loading}
            >
              <option value="">Choose a date...</option>
              {availableDates.map(date => (
                <option key={date} value={date}>
                  {formatDate(date)}
                </option>
              ))}
            </select>
          </div>
          
          <div className="flex items-end">
            <button
              onClick={() => fetchHistoricalData(selectedDate)}
              disabled={loading || !selectedDate}
              className="btn btn-primary disabled:opacity-50"
            >
              {loading ? 'Loading...' : 'Load Data'}
            </button>
          </div>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-8">
          <div className="text-red-800">
            <h3 className="text-lg font-medium">Error</h3>
            <p className="mt-1">{error}</p>
          </div>
        </div>
      )}

      {/* Historical Data */}
      {historicalData && (
        <div>
          {/* Summary */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="card">
              <div className="text-center">
                <div className="text-3xl font-bold text-blue-600">{historicalData.count}</div>
                <div className="text-sm text-gray-600 mt-1">Total Recommendations</div>
              </div>
            </div>
            
            <div className="card">
              <div className="text-center">
                <div className="text-lg font-semibold text-gray-900">
                  {formatDate(historicalData.date)}
                </div>
                <div className="text-sm text-gray-600 mt-1">Analysis Date</div>
              </div>
            </div>
            
            <div className="card">
              <div className="text-center">
                <div className="text-lg font-semibold text-gray-900">
                  {new Date(historicalData.timestamp).toLocaleTimeString()}
                </div>
                <div className="text-sm text-gray-600 mt-1">Analysis Time</div>
              </div>
            </div>

            {/* Reconciliation Performance Summary */}
            <div className="card">
              <div className="text-center">
                <div className="text-lg font-semibold text-gray-900">
                  {(() => {
                    const recs = historicalData.recommendations || []
                    const targetsMet = recs.filter(r => r.result_status === 'target_met').length
                    const stopLossHit = recs.filter(r => r.result_status === 'stop_loss_hit').length
                    const inTransit = recs.filter(r => r.result_status === 'in_transit').length
                    
                    return (
                      <div>
                        <div className="text-green-600 font-bold">{targetsMet} ✅</div>
                        <div className="text-red-600">{stopLossHit} ❌</div>
                        <div className="text-yellow-600">{inTransit} ⏳</div>
                      </div>
                    )
                  })()}
                </div>
                <div className="text-sm text-gray-600 mt-1">Performance Results</div>
              </div>
            </div>
          </div>

          {/* Recommendations Table */}
          <div>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Recommendations for {formatDate(historicalData.date)}
            </h2>
            
            {historicalData.recommendations && historicalData.recommendations.length > 0 ? (
              <EnhancedRecommendationTable recommendations={historicalData.recommendations} />
            ) : (
              <div className="card">
                <div className="text-center py-12">
                  <div className="text-gray-400 mb-4">
                    <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No recommendations found</h3>
                  <p className="text-gray-600">
                    There were no stock recommendations on this date.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Loading State */}
      {loading && !historicalData && (
        <div className="card">
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-3 text-gray-600">Loading historical data...</span>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!loading && !historicalData && !error && (
        <div className="card">
          <div className="text-center py-12">
            <div className="text-gray-400 mb-4">
              <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Select a Date</h3>
            <p className="text-gray-600">
              Choose a date from the dropdown above to view historical recommendations.
            </p>
          </div>
        </div>
      )}
    </div>
  )
}

export default History
