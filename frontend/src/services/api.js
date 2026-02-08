// API service for communicating with Lambda backend and direct S3 access

// Environment detection - CRITICAL for AWS deployment safety
const isLocalDev = import.meta.env.DEV || window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'

// Use environment-specific URLs based on deployment context
const API_BASE_URL = isLocalDev 
  ? (import.meta.env.REACT_APP_API_BASE_URL_LOCAL || 'http://localhost:8000')
  : (import.meta.env.REACT_APP_API_BASE_URL_AWS || 'https://8s0seutfrh.execute-api.us-east-1.amazonaws.com')

const S3_BUCKET_URL = isLocalDev
  ? `https://${import.meta.env.REACT_APP_S3_BUCKET_LOCAL || '7h-stock-analyzer-dev'}.s3.us-east-1.amazonaws.com`
  : `https://${import.meta.env.REACT_APP_S3_BUCKET_PROD || '7h-stock-analyzer'}.s3.us-east-1.amazonaws.com`

// Use CloudFront for production, S3 bucket for local development
const CLOUDFRONT_URL = isLocalDev 
  ? 'http://localhost:8000'  // Local development
  : (import.meta.env.REACT_APP_CLOUDFRONT_URL || 'https://d37m5zz5fkglhg.cloudfront.net')  // AWS production

// Use appropriate data URL: S3 bucket for configs, CloudFront/API for other data
const S3_DATA_URL = isLocalDev 
  ? S3_BUCKET_URL  // Use S3 dev bucket for config files in local development
  : CLOUDFRONT_URL  // Use CloudFront for production

// Get API key from localStorage or parent component
let currentApiKey = localStorage.getItem('stockAnalyzerApiKey') || ''

export const setApiKey = (key) => {
  currentApiKey = key
}

// Helper function to add API key to headers
const getHeaders = () => {
  const headers = {
    'Content-Type': 'application/json'
  }
  
  if (currentApiKey) {
    headers['X-API-Key'] = currentApiKey
  }
  
  return headers
}

// Direct S3 access - Optimized for read operations
export const s3Api = {
  // Latest recommendations from S3 (direct access)
  getLatestRecommendations: async () => {
    try {
      // For local development, use Lambda endpoint instead of S3
      const url = isLocalDev 
        ? `${API_BASE_URL}/recommendations`
        : `${S3_DATA_URL}/data/latest.json`
      
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Cache-Control': 'no-cache'
        }
      })
      if (!response.ok) {
        throw new Error('Failed to fetch latest recommendations')
      }
      return response.json()
    } catch (error) {
      // Fallback to Lambda if S3 fails
      console.warn('Data access failed, falling back to Lambda:', error)
      return lambdaApi.getLatestRecommendations()
    }
  },

  // Historical recommendations from S3 (direct access)
  getHistoricalRecommendations: async (date) => {
    try {
      const response = await fetch(`${S3_DATA_URL}/data/daily/${date}.json`)
      if (!response.ok) {
        throw new Error('Failed to fetch historical recommendations from S3')
      }
      return response.json()
    } catch (error) {
      // Fallback to Lambda if S3 fails
      console.warn('S3 direct access failed, falling back to Lambda:', error)
      return lambdaApi.getHistoricalRecommendations(date)
    }
  },

  // Enhanced historical data from S3 (direct access)
  getHistoricalRecommendationsEnhanced: async (date) => {
    try {
      const response = await fetch(`${S3_DATA_URL}/data/enhanced/${date}.json`)
      if (!response.ok) {
        throw new Error('Failed to fetch enhanced historical recommendations from S3')
      }
      return response.json()
    } catch (error) {
      // Fallback to Lambda if S3 fails
      console.warn('S3 direct access failed, falling back to Lambda:', error)
      return lambdaApi.getHistoricalRecommendationsEnhanced(date)
    }
  },

  // List available dates from S3
  listAvailableDates: async () => {
    try {
      const response = await fetch(`${S3_DATA_URL}/data/dates.json`)
      if (!response.ok) {
        throw new Error('Failed to fetch available dates from S3')
      }
      return response.json()
    } catch (error) {
      // Fallback to Lambda if S3 fails
      console.warn('S3 direct access failed, falling back to Lambda:', error)
      return lambdaApi.listAvailableDates()
    }
  },

  // Reconciliation data from S3 (direct access)
  getReconciliationSummary: async () => {
    try {
      const response = await fetch(`${S3_DATA_URL}/recon/summary.json`)
      if (!response.ok) {
        throw new Error('Failed to fetch reconciliation summary from S3')
      }
      return response.json()
    } catch (error) {
      // Fallback to Lambda if S3 fails
      console.warn('S3 direct access failed, falling back to Lambda:', error)
      return lambdaApi.getReconciliationSummary()
    }
  },

  getDailyReconciliation: async (date) => {
    try {
      const response = await fetch(`${S3_DATA_URL}/recon/daily/${date}.json`)
      if (!response.ok) {
        throw new Error('Failed to fetch daily reconciliation from S3')
      }
      return response.json()
    } catch (error) {
      // Fallback to Lambda if S3 fails
      console.warn('S3 direct access failed, falling back to Lambda:', error)
      return lambdaApi.getDailyReconciliation(date)
    }
  },

  // Configuration from backend API (consistent pattern)
  getConfig: async (configType) => {
    try {
      const response = await fetch(`${API_BASE_URL}/config/${configType}`, {
        headers: getHeaders()
      })
      if (!response.ok) {
        throw new Error('Failed to fetch configuration')
      }
      return response.json()
    } catch (error) {
      // Fallback to Lambda if API fails
      console.warn('API config access failed, falling back to Lambda:', error)
      return lambdaApi.getConfig(configType)
    }
  },

  getAllConfigs: async () => {
    try {
      const configTypes = ['portfolio', 'watchlist', 'us_stocks', 'etfs']
      const configs = {}
      
      for (const configType of configTypes) {
        try {
          // Use backend API for config access (consistent pattern)
          const response = await fetch(`${API_BASE_URL}/config/${configType}`, {
            headers: getHeaders()
          })
          if (response.ok) {
            const configData = await response.json()
            configs[configType] = configData
          } else {
            configs[configType] = {
              success: false,
              symbols: [],
              error: 'Configuration not found'
            }
          }
        } catch (error) {
          configs[configType] = {
            success: false,
            symbols: [],
            error: 'Configuration not available'
          }
        }
      }
      
      return {
        success: true,
        configs: configs
      }
    } catch (error) {
      throw new Error(`Failed to fetch configurations: ${error.message}`)
    }
  }
}

// Lambda API - Write operations and fallback
export const lambdaApi = {
  getLatestRecommendations: async () => {
    const response = await fetch(`${API_BASE_URL}/recommendations`, {
      headers: getHeaders()
    })
    if (!response.ok) {
      throw new Error('Failed to fetch latest recommendations')
    }
    return response.json()
  },

  getHistoricalRecommendations: async (date) => {
    const response = await fetch(`${API_BASE_URL}/history/${date}`, {
      headers: getHeaders()
    })
    if (!response.ok) {
      throw new Error('Failed to fetch historical recommendations')
    }
    return response.json()
  },

  getHistoricalRecommendationsEnhanced: async (date) => {
    const response = await fetch(`${API_BASE_URL}/history/${date}/enhanced`, {
      headers: getHeaders()
    })
    if (!response.ok) {
      throw new Error('Failed to fetch enhanced historical recommendations')
    }
    return response.json()
  },

  listAvailableDates: async () => {
    const response = await fetch(`${API_BASE_URL}/history/dates`, {
      headers: getHeaders()
    })
    if (!response.ok) {
      throw new Error('Failed to fetch available dates')
    }
    return response.json()
  },

  triggerManualRun: async () => {
    const response = await fetch(`${API_BASE_URL}/run-now`, {
      method: 'POST',
      headers: getHeaders()
    })
    if (!response.ok) {
      throw new Error('Failed to trigger manual run')
    }
    return response.json()
  },

  healthCheck: async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/health`, {
        headers: getHeaders()
      })
      if (!response.ok) {
        throw new Error('Health check failed')
      }
      return response.json()
    } catch (error) {
      // Fallback for when backend is not available
      return {
        status: 'healthy',
        message: 'Backend not available - using static data',
        timestamp: new Date().toISOString()
      }
    }
  },

  // Reconciliation data via Lambda
  getReconciliationSummary: async () => {
    const response = await fetch(`${API_BASE_URL}/recon/summary`, {
      headers: getHeaders()
    })
    if (!response.ok) {
      throw new Error('Failed to fetch reconciliation summary')
    }
    return response.json()
  },

  getDailyReconciliation: async (date) => {
    const response = await fetch(`${API_BASE_URL}/recon/daily/${date}`, {
      headers: getHeaders()
    })
    if (!response.ok) {
      throw new Error('Failed to fetch daily reconciliation')
    }
    return response.json()
  },

  // Configuration management via Lambda
  getConfig: async (configType) => {
    const response = await fetch(`${API_BASE_URL}/config/${configType}`, {
      headers: getHeaders()
    })
    if (!response.ok) {
      throw new Error('Failed to fetch configuration')
    }
    return response.json()
  },

  getAllConfigs: async () => {
    const configTypes = ['portfolio', 'watchlist', 'us_stocks', 'etfs']
    const configs = {}
    
    for (const configType of configTypes) {
      try {
        // Use backend API for config access (consistent with local dev)
        const response = await fetch(`${API_BASE_URL}/config/${configType}`, {
          headers: getHeaders()
        })
        if (response.ok) {
          const apiData = await response.json()
          configs[configType] = apiData
        } else {
          configs[configType] = {
            success: false,
            symbols: [],
            error: 'Configuration not found'
          }
        }
      } catch (error) {
        configs[configType] = {
          success: false,
          symbols: [],
          error: 'Configuration not available'
        }
      }
    }
    
    return {
      success: true,
      configs: configs
    }
  },

  updateConfig: async (configType, symbols, backup = true) => {
    const response = await fetch(`${API_BASE_URL}/config/update`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({
        config_type: configType,
        symbols: symbols,
        backup: backup
      })
    })
    if (!response.ok) {
      throw new Error('Failed to update configuration')
    }
    return response.json()
  },

  validateSymbols: async (symbols) => {
    const response = await fetch(`${API_BASE_URL}/config/validate`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({
        symbols: symbols
      })
    })
    if (!response.ok) {
      throw new Error('Failed to validate symbols')
    }
    return response.json()
  },

}

// Hybrid API interface - Direct S3 for reads, Lambda for writes
export const api = {
  // Read operations - Use S3 direct access with Lambda fallback
  getLatestRecommendations: s3Api.getLatestRecommendations,
  getHistoricalRecommendations: s3Api.getHistoricalRecommendations,
  getHistoricalRecommendationsEnhanced: s3Api.getHistoricalRecommendationsEnhanced,
  listAvailableDates: s3Api.listAvailableDates,
  getReconciliationSummary: s3Api.getReconciliationSummary,
  getDailyReconciliation: s3Api.getDailyReconciliation,
  getConfig: s3Api.getConfig,
  getAllConfigs: s3Api.getAllConfigs,
  
  // Write operations - Must go through Lambda (for security and authentication)
  triggerManualRun: lambdaApi.triggerManualRun,
  updateConfig: lambdaApi.updateConfig,
  validateSymbols: lambdaApi.validateSymbols,
  
  // Health check - Lambda only
  getHealth: lambdaApi.healthCheck,
  
  // API key management
  setApiKey: setApiKey
}

// Utility functions
export const formatPrice = (price) => {
  if (price === null || price === undefined) return 'N/A'
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD'
  }).format(price)
}

export const formatPercentage = (pct) => {
  if (pct === null || pct === undefined) return 'N/A'
  return `${pct >= 0 ? '+' : ''}${pct.toFixed(2)}%`
}

export const getRecommendationColor = (recommendation) => {
  switch (recommendation) {
    case 'Strong Buy':
    case 'Buy':
      return 'text-green-600'
    case 'Strong Sell':
    case 'Sell':
      return 'text-red-600'
    case 'Hold':
      return 'text-yellow-600'
    default:
      return 'text-gray-600'
  }
}

export const getRecommendationBadgeColor = (recommendation) => {
  switch (recommendation) {
    case 'Strong Buy':
      return 'bg-green-100 text-green-800'
    case 'Buy':
      return 'bg-green-50 text-green-700'
    case 'Strong Sell':
      return 'bg-red-100 text-red-800'
    case 'Sell':
      return 'bg-red-50 text-red-700'
    case 'Hold':
      return 'bg-yellow-50 text-yellow-700'
    default:
      return 'bg-gray-50 text-gray-700'
  }
}

// Enhanced utility functions for new features
export const getConfidenceColor = (confidence) => {
  switch (confidence) {
    case 'High':
      return 'bg-green-100 text-green-800 border-green-300'
    case 'Medium':
      return 'bg-yellow-100 text-yellow-800 border-yellow-300'
    case 'Low':
      return 'bg-red-100 text-red-800 border-red-300'
    default:
      return 'bg-gray-100 text-gray-800 border-gray-300'
  }
}

export const formatNumber = (num, decimals = 2) => {
  if (num === null || num === undefined) return 'N/A'
  if (num >= 1000000000) {
    return (num / 1000000000).toFixed(decimals) + 'B'
  } else if (num >= 1000000) {
    return (num / 1000000).toFixed(decimals) + 'M'
  } else if (num >= 1000) {
    return (num / 1000).toFixed(decimals) + 'K'
  }
  return num.toFixed(decimals)
}

export const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

export const formatDateTime = (dateString) => {
  return new Date(dateString).toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}
