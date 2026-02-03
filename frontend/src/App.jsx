import React, { useState, useEffect } from 'react'
import Dashboard from './pages/Dashboard'
import History from './pages/History'
import Config from './pages/Config'
import { api } from './services/api'

function App() {
  const [currentPage, setCurrentPage] = useState('dashboard')
  const [recommendations, setRecommendations] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [lastUpdated, setLastUpdated] = useState(null)
  const [systemHealth, setSystemHealth] = useState(null)

  useEffect(() => {
    fetchLatestRecommendations()
    fetchSystemHealth()
    // Auto-refresh every 5 minutes
    const interval = setInterval(() => {
      fetchLatestRecommendations()
      fetchSystemHealth()
    }, 300000)
    return () => clearInterval(interval)
  }, [])

  const fetchLatestRecommendations = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await api.getLatestRecommendations()
      setRecommendations(data.recommendations || [])
      setLastUpdated(data.timestamp)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const fetchSystemHealth = async () => {
    try {
      const health = await api.getHealth()
      setSystemHealth(health)
    } catch (err) {
      console.error('Failed to fetch system health:', err)
    }
  }

  const triggerManualRun = async () => {
    try {
      setLoading(true)
      setError(null)
      await api.triggerManualRun()
      // Wait a moment then refresh
      setTimeout(() => {
        fetchLatestRecommendations()
        fetchSystemHealth()
      }, 3000)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const renderNavigation = () => (
    <nav className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <div className="flex-shrink-0 flex items-center">
              <h1 className="text-xl font-bold text-gray-900">7H Stock Analyzer</h1>
              {systemHealth && (
                <span className={`ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  systemHealth.status === 'healthy' 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-red-100 text-red-800'
                }`}>
                  {systemHealth.status === 'healthy' ? '●' : '●'} {systemHealth.status}
                </span>
              )}
            </div>
            <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
              <button
                onClick={() => setCurrentPage('dashboard')}
                className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                  currentPage === 'dashboard'
                    ? 'border-indigo-500 text-gray-900'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Dashboard
              </button>
              <button
                onClick={() => setCurrentPage('history')}
                className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                  currentPage === 'history'
                    ? 'border-indigo-500 text-gray-900'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                History
              </button>
              <button
                onClick={() => setCurrentPage('config')}
                className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                  currentPage === 'config'
                    ? 'border-indigo-500 text-gray-900'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Configuration
              </button>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            {lastUpdated && (
              <span className="text-sm text-gray-500">
                Last updated: {new Date(lastUpdated).toLocaleString()}
              </span>
            )}
            <button
              onClick={triggerManualRun}
              disabled={loading}
              className="btn btn-primary disabled:opacity-50"
            >
              {loading ? 'Running...' : 'Run Now'}
            </button>
          </div>
        </div>
      </div>
    </nav>
  )

  const renderContent = () => {
    if (error) {
      return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <div className="text-red-800">
              <h3 className="text-lg font-medium">Error</h3>
              <p className="mt-1">{error}</p>
              <button
                onClick={fetchLatestRecommendations}
                className="mt-3 btn btn-primary"
              >
                Retry
              </button>
            </div>
          </div>
        </div>
      )
    }

    switch (currentPage) {
      case 'dashboard':
        return (
          <Dashboard
            recommendations={recommendations}
            loading={loading}
            onRefresh={fetchLatestRecommendations}
            systemHealth={systemHealth}
          />
        )
      case 'history':
        return <History />
      case 'config':
        return <Config />
      default:
        return null
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {renderNavigation()}
      {renderContent()}
    </div>
  )
}

export default App
