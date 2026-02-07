// API service for communicating with S3 and Lambda

const S3_BUCKET = import.meta.env.REACT_APP_S3_BUCKET || '7h-stock-analyzer'
const API_BASE_URL = import.meta.env.REACT_APP_API_BASE_URL || 'http://localhost:8000'
const S3_REGION = import.meta.env.REACT_APP_S3_REGION || 'us-east-1'

// Check if we're in development mode
const isDevelopment = import.meta.env.MODE === 'development'

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

// S3 API - Direct S3 access for static data
export const s3Api = {
  getLatestRecommendations: async () => {
    if (isDevelopment) {
      // Use local API for development
      const response = await fetch(`${API_BASE_URL}/recommendations`, {
        headers: getHeaders()
      })
      if (!response.ok) {
        throw new Error('Failed to fetch latest recommendations')
      }
      return response.json()
    }
    
    const response = await fetch(`http://${S3_BUCKET}.s3-website-${S3_REGION}.amazonaws.com/data/latest.json`)
    if (!response.ok) {
      throw new Error('Failed to fetch latest recommendations')
    }
    return response.json()
  },

  getHistoricalRecommendations: async (date) => {
    if (isDevelopment) {
      // Use local API for development
      const response = await fetch(`${API_BASE_URL}/history/${date}`, {
        headers: getHeaders()
      })
      if (!response.ok) {
        throw new Error('Failed to fetch historical recommendations')
      }
      return response.json()
    }
    
    const response = await fetch(`http://${S3_BUCKET}.s3-website-${S3_REGION}.amazonaws.com/data/daily/${date}.json`)
    if (!response.ok) {
      throw new Error('Failed to fetch historical recommendations')
    }
    return response.json()
  },

  getHistoricalRecommendationsEnhanced: async (date) => {
    // Use direct S3 access for enhanced historical data
    if (isDevelopment) {
      // In development, still use API for testing
      const response = await fetch(`${API_BASE_URL}/history/${date}/enhanced`, {
        headers: getHeaders()
      })
      if (!response.ok) {
        throw new Error('Failed to fetch enhanced historical recommendations')
      }
      return response.json()
    }
    
    // Production: Direct S3 access
    const s3Url = `http://${S3_BUCKET}.s3-website-${S3_REGION}.amazonaws.com/data/enhanced/${date}.json`
    const response = await fetch(s3Url)
    if (!response.ok) {
      // Fallback to API if S3 file doesn't exist
      const apiResponse = await fetch(`${API_BASE_URL}/history/${date}/enhanced`, {
        headers: getHeaders()
      })
      if (!apiResponse.ok) {
        throw new Error('Failed to fetch enhanced historical recommendations')
      }
      return apiResponse.json()
    }
    return response.json()
  },

  listAvailableDates: async () => {
    // This would require a Lambda function to list S3 objects
    // For now, return a mock implementation
    const response = await fetch(`${API_BASE_URL}/history/dates`, {
      headers: getHeaders()
    })
    if (!response.ok) {
      throw new Error('Failed to fetch available dates')
    }
    return response.json()
  }
}

// Lambda API - For operations that need Lambda functions
export const lambdaApi = {
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

  // Reconciliation data via direct S3 access
  getReconciliationSummary: async () => {
    // Use direct S3 access for reconciliation summary
    if (isDevelopment) {
      // In development, still use API for testing
      const response = await fetch(`${API_BASE_URL}/recon/summary`, {
        headers: getHeaders()
      })
      if (!response.ok) {
        throw new Error('Failed to fetch reconciliation summary')
      }
      return response.json()
    }
    
    // Production: Direct S3 access
    const s3Url = `http://${S3_BUCKET}.s3-website-${S3_REGION}.amazonaws.com/recon/summary.json`
    const response = await fetch(s3Url)
    if (!response.ok) {
      // Fallback to API if S3 file doesn't exist
      const apiResponse = await fetch(`${API_BASE_URL}/recon/summary`, {
        headers: getHeaders()
      })
      if (!apiResponse.ok) {
        throw new Error('Failed to fetch reconciliation summary')
      }
      return apiResponse.json()
    }
    return response.json()
  },

  getDailyReconciliation: async (date) => {
    // Use direct S3 access for daily reconciliation data
    if (isDevelopment) {
      // In development, still use API for testing
      const response = await fetch(`${API_BASE_URL}/recon/daily/${date}`, {
        headers: getHeaders()
      })
      if (!response.ok) {
        throw new Error('Failed to fetch daily reconciliation')
      }
      return response.json()
    }
    
    // Production: Direct S3 access
    const s3Url = `http://${S3_BUCKET}.s3-website-${S3_REGION}.amazonaws.com/recon/daily/${date}.json`
    const response = await fetch(s3Url)
    if (!response.ok) {
      // Fallback to API if S3 file doesn't exist
      const apiResponse = await fetch(`${API_BASE_URL}/recon/daily/${date}`, {
        headers: getHeaders()
      })
      if (!apiResponse.ok) {
        throw new Error('Failed to fetch daily reconciliation')
      }
      return apiResponse.json()
    }
    return response.json()
  },

  // Configuration management - Read directly from S3 TXT files
  getConfig: async (configType) => {
    try {
      // Use S3 website endpoint for direct access to TXT files
      const s3Url = `http://${S3_BUCKET}.s3-website-${S3_REGION}.amazonaws.com/config/config_${configType}.txt`
      const response = await fetch(s3Url)
      
      if (!response.ok) {
        // If S3 fails, try API as fallback
        const apiResponse = await fetch(`${API_BASE_URL}/config/${configType}`, {
          headers: getHeaders()
        })
        if (!apiResponse.ok) {
          throw new Error('Failed to fetch configuration')
        }
        return apiResponse.json()
      }
      
      // Parse TXT file - each line is a symbol
      const text = await response.text()
      const symbols = text.split('\n')
        .map(line => line.trim())
        .filter(line => line && !line.startsWith('#') && !line.startsWith('//'))
      
      return {
        success: true,
        symbols: symbols,
        source: 's3'
      }
    } catch (error) {
      // Final fallback to API
      try {
        const apiResponse = await fetch(`${API_BASE_URL}/config/${configType}`, {
          headers: getHeaders()
        })
        if (!apiResponse.ok) {
          throw new Error('Failed to fetch configuration')
        }
        return apiResponse.json()
      } catch (apiError) {
        return handleApiError(apiError, {
          success: false,
          error: 'Configuration not available',
          symbols: []
        })
      }
    }
  },

  getAllConfigs: async () => {
    const configTypes = ['portfolio', 'watchlist', 'us_stocks', 'etfs']
    const configs = {}
    
    for (const configType of configTypes) {
      try {
        // Use S3 website endpoint for direct access to TXT files
        const s3Url = `http://${S3_BUCKET}.s3-website-${S3_REGION}.amazonaws.com/config/config_${configType}.txt`
        const response = await fetch(s3Url)
        
        if (response.ok) {
          // Parse TXT file - each line is a symbol
          const text = await response.text()
          const symbols = text.split('\n')
            .map(line => line.trim())
            .filter(line => line && !line.startsWith('#') && !line.startsWith('//'))
          
          configs[configType] = {
            success: true,
            symbols: symbols,
            source: 's3'
          }
        } else {
          // Try API as fallback
          const apiResponse = await fetch(`${API_BASE_URL}/config/${configType}`, {
            headers: getHeaders()
          })
          if (apiResponse.ok) {
            const apiData = await apiResponse.json()
            configs[configType] = apiData
          } else {
            configs[configType] = {
              success: false,
              symbols: [],
              error: 'Configuration not found'
            }
          }
        }
      } catch (error) {
        // Final fallback to API or empty config
        try {
          const apiResponse = await fetch(`${API_BASE_URL}/config/${configType}`, {
            headers: getHeaders()
          })
          if (apiResponse.ok) {
            const apiData = await apiResponse.json()
            configs[configType] = apiData
          } else {
            configs[configType] = {
              success: false,
              symbols: [],
              error: 'Configuration not available'
            }
          }
        } catch (apiError) {
          configs[configType] = {
            success: false,
            symbols: [],
            error: 'Configuration not available'
          }
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

  syncConfigs: async () => {
    const response = await fetch(`${API_BASE_URL}/config/sync`, {
      method: 'POST',
      headers: getHeaders()
    })
    if (!response.ok) {
      throw new Error('Failed to sync configurations')
    }
    return response.json()
  }
}

// Combined API interface
export const api = {
  getLatestRecommendations: s3Api.getLatestRecommendations,
  getHistoricalRecommendations: s3Api.getHistoricalRecommendations,
  getHistoricalRecommendationsEnhanced: s3Api.getHistoricalRecommendationsEnhanced,
  triggerManualRun: lambdaApi.triggerManualRun,
  getHealth: lambdaApi.healthCheck,
  getReconciliationSummary: lambdaApi.getReconciliationSummary,
  getDailyReconciliation: lambdaApi.getDailyReconciliation,
  getConfig: lambdaApi.getConfig,
  getAllConfigs: lambdaApi.getAllConfigs,
  updateConfig: lambdaApi.updateConfig,
  validateSymbols: lambdaApi.validateSymbols,
  syncConfigs: lambdaApi.syncConfigs,
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
