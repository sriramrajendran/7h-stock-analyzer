import React, { useState, useEffect } from 'react'
import Dashboard from './pages/Dashboard'
import History from './pages/History'
import Config from './pages/Config'
import ApiKeyModal from './components/ApiKeyModal'
import { api } from './services/api'

function App() {
  const [currentPage, setCurrentPage] = useState('dashboard')
  const [recommendations, setRecommendations] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [lastUpdated, setLastUpdated] = useState(null)
  const [systemHealth, setSystemHealth] = useState(null)
  const [showApiKeyModal, setShowApiKeyModal] = useState(false)
  const [hasApiKey, setHasApiKey] = useState(false)

  useEffect(() => {
    // Check if API key exists on mount
    const savedKey = localStorage.getItem('stockAnalyzerApiKey')
    if (savedKey) {
      setHasApiKey(true)
      api.setApiKey(savedKey)
    } else {
      setShowApiKeyModal(true)
    }
  }, [])

  useEffect(() => {
    if (hasApiKey) {
      fetchLatestRecommendations()
      fetchSystemHealth()
    }
    // Auto-refresh recommendations every 5 minutes, health check every 10 minutes
    const recommendationsInterval = hasApiKey ? setInterval(() => {
      fetchLatestRecommendations()
    }, 300000) : null
    const healthInterval = hasApiKey ? setInterval(() => {
      fetchSystemHealth()
    }, 600000) : null
    return () => {
      if (recommendationsInterval) clearInterval(recommendationsInterval)
      if (healthInterval) clearInterval(healthInterval)
    }
  }, [hasApiKey])

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
    // Cache health check for 2 minutes to reduce API calls
    const now = Date.now()
    const lastHealthCheck = localStorage.getItem('lastHealthCheck')
    const cachedHealth = localStorage.getItem('cachedHealth')
    
    if (lastHealthCheck && cachedHealth && (now - parseInt(lastHealthCheck)) < 120000) {
      setSystemHealth(JSON.parse(cachedHealth))
      return
    }
    
    try {
      const health = await api.getHealth()
      setSystemHealth(health)
      localStorage.setItem('cachedHealth', JSON.stringify(health))
      localStorage.setItem('lastHealthCheck', now.toString())
    } catch (err) {
      console.error('Failed to fetch system health:', err)
      // Use cached health if available, even if expired
      if (cachedHealth) {
        setSystemHealth(JSON.parse(cachedHealth))
      }
    }
  }

  const handleApiKeySet = (apiKey) => {
    api.setApiKey(apiKey)
    setHasApiKey(true)
    setShowApiKeyModal(false)
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
              <img src="/stock-icon.svg" alt="7H Stock Analyzer" className="h-8 w-8 mr-2" />
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
              <button
                onClick={() => setShowApiKeyModal(true)}
                className="inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              >
                🔑 API Key
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
    if (!hasApiKey) {
      return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="bg-yellow-50 border border-yellow-200 rounded-md p-6">
            <div className="text-yellow-800">
              <h3 className="text-lg font-medium mb-2">API Key Required</h3>
              <p className="mb-4">
                Please set your API key to access the stock analyzer features.
              </p>
              <button
                onClick={() => setShowApiKeyModal(true)}
                className="btn btn-primary"
              >
                Set API Key
              </button>
            </div>
          </div>
        </div>
      )
    }

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
      <ApiKeyModal
        isOpen={showApiKeyModal}
        onClose={() => setShowApiKeyModal(false)}
        onApiKeySet={handleApiKeySet}
      />
    </div>
  )
}

export default App
