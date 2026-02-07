import React, { useState, useEffect } from 'react'
import { api } from '../services/api'

const Config = () => {
  const [configs, setConfigs] = useState({})
  const [selectedConfig, setSelectedConfig] = useState('portfolio')
  const [symbols, setSymbols] = useState([])
  const [newSymbol, setNewSymbol] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)
  const [validationResults, setValidationResults] = useState(null)

  const configTypes = [
    { value: 'portfolio', label: 'Portfolio', description: 'Your main portfolio stocks' },
    { value: 'watchlist', label: 'Watchlist', description: 'Stocks you are monitoring' },
    { value: 'us_stocks', label: 'US Stocks', description: 'Major US market stocks' },
    { value: 'etfs', label: 'ETFs', description: 'Exchange-traded funds' }
  ]

  useEffect(() => {
    fetchAllConfigs()
  }, [])

  const fetchAllConfigs = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await api.getAllConfigs()
      setConfigs(data.configs || {})
      
      // Load symbols for selected config
      if (data.configs && data.configs[selectedConfig]) {
        const configData = data.configs[selectedConfig]
        setSymbols(configData.success ? configData.symbols || [] : [])
      }

      // Show success message if data loaded from S3
      const hasS3Data = Object.values(data.configs || {}).some(config => config.source === 's3')
      if (hasS3Data) {
        setSuccess('Configuration loaded from S3 successfully!')
        setTimeout(() => setSuccess(null), 3000)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const fetchConfig = async (configType) => {
    try {
      setLoading(true)
      setError(null)
      const data = await api.getConfig(configType)
      if (data.success) {
        setSymbols(data.symbols || [])
        setConfigs(prev => ({
          ...prev,
          [configType]: data
        }))
      } else {
        setError(data.error)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (configs[selectedConfig]) {
      const configData = configs[selectedConfig]
      setSymbols(configData.success ? configData.symbols || [] : [])
    } else {
      fetchConfig(selectedConfig)
    }
  }, [selectedConfig])

  const handleConfigChange = (configType) => {
    setSelectedConfig(configType)
    setValidationResults(null)
    setSuccess(null)
  }

  const addSymbol = () => {
    const symbol = newSymbol.toUpperCase().trim()
    if (symbol && !symbols.includes(symbol)) {
      setSymbols([...symbols, symbol])
      setNewSymbol('')
      setValidationResults(null)
    }
  }

  const removeSymbol = (symbolToRemove) => {
    setSymbols(symbols.filter(s => s !== symbolToRemove))
    setValidationResults(null)
  }

  const validateSymbols = async () => {
    if (symbols.length === 0) {
      setError('No symbols to validate')
      return
    }

    try {
      setLoading(true)
      setError(null)
      const results = await api.validateSymbols(symbols)
      setValidationResults(results)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const saveConfig = async () => {
    if (symbols.length === 0) {
      setError('Cannot save empty configuration')
      return
    }

    try {
      setLoading(true)
      setError(null)
      setSuccess(null)
      
      const result = await api.updateConfig(selectedConfig, symbols, true)
      
      if (result.success) {
        setSuccess('Configuration saved successfully!')
        // Refresh configs
        await fetchAllConfigs()
      } else {
        setError(result.error)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const syncConfigs = async () => {
    try {
      setLoading(true)
      setError(null)
      setSuccess(null)
      
      const result = await api.syncConfigs()
      
      if (result.success) {
        setSuccess('Configurations synced successfully!')
        await fetchAllConfigs()
      } else {
        setError(result.error)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const getConfigInfo = () => {
    return configTypes.find(c => c.value === selectedConfig) || configTypes[0]
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Configuration Management</h1>
        <p className="mt-2 text-gray-600">
          Manage stock symbols for different analysis categories
        </p>
      </div>

      {/* Error and Success Messages */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-6">
          <div className="text-red-800">
            <h3 className="text-lg font-medium">Error</h3>
            <p className="mt-1">{error}</p>
          </div>
        </div>
      )}

      {success && (
        <div className="bg-green-50 border border-green-200 rounded-md p-4 mb-6">
          <div className="text-green-800">
            <h3 className="text-lg font-medium">Success</h3>
            <p className="mt-1">{success}</p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Configuration Type Selector */}
        <div className="lg:col-span-1">
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Configuration Type</h2>
            <div className="space-y-2">
              {configTypes.map(config => (
                <button
                  key={config.value}
                  onClick={() => handleConfigChange(config.value)}
                  className={`w-full text-left px-4 py-3 rounded-md border transition-colors ${
                    selectedConfig === config.value
                      ? 'border-blue-500 bg-blue-50 text-blue-900'
                      : 'border-gray-200 hover:border-gray-300 text-gray-700'
                  }`}
                >
                  <div className="font-medium">{config.label}</div>
                  <div className="text-sm text-gray-500">{config.description}</div>
                  {configs[config.value] && configs[config.value].success && (
                    <div className="text-xs text-gray-400 mt-1">
                      {configs[config.value].count} symbols
                    </div>
                  )}
                </button>
              ))}
            </div>
            
            <div className="mt-6 pt-6 border-t">
              <button
                onClick={syncConfigs}
                disabled={loading}
                className="w-full btn btn-secondary disabled:opacity-50"
              >
                {loading ? 'Syncing...' : 'Sync All Configs'}
              </button>
            </div>
          </div>
        </div>

        {/* Symbol Editor */}
        <div className="lg:col-span-2">
          <div className="card">
            <div className="flex justify-between items-center mb-6">
              <div>
                <h2 className="text-lg font-semibold text-gray-900">
                  {getConfigInfo().label} Configuration
                </h2>
                <p className="text-sm text-gray-600">{getConfigInfo().description}</p>
              </div>
              <div className="text-sm text-gray-500">
                {symbols.length} symbols
              </div>
            </div>

            {/* Add Symbol */}
            <div className="mb-6">
              <div className="flex space-x-2">
                <input
                  type="text"
                  value={newSymbol}
                  onChange={(e) => setNewSymbol(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && addSymbol()}
                  placeholder="Enter stock symbol (e.g., AAPL)"
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
                <button
                  onClick={addSymbol}
                  disabled={!newSymbol.trim()}
                  className="btn btn-primary disabled:opacity-50"
                >
                  Add
                </button>
              </div>
            </div>

            {/* Symbol List */}
            <div className="mb-6">
              <div className="max-h-64 overflow-y-auto border border-gray-200 rounded-md">
                {symbols.length === 0 ? (
                  <div className="p-4 text-center text-gray-500">
                    No symbols added yet
                  </div>
                ) : (
                  <div className="divide-y divide-gray-200">
                    {symbols.map((symbol, index) => (
                      <div key={index} className="flex items-center justify-between p-3 hover:bg-gray-50">
                        <span className="font-medium text-gray-900">{symbol}</span>
                        <button
                          onClick={() => removeSymbol(symbol)}
                          className="text-red-600 hover:text-red-800 text-sm"
                        >
                          Remove
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Validation Results */}
            {validationResults && (
              <div className="mb-6 p-4 bg-gray-50 rounded-md">
                <h3 className="text-sm font-medium text-gray-900 mb-2">Validation Results</h3>
                <div className="text-sm text-gray-600">
                  <div>Valid symbols: {validationResults.valid_count}</div>
                  <div>Invalid symbols: {validationResults.invalid_count}</div>
                  {validationResults.invalid_symbols && validationResults.invalid_symbols.length > 0 && (
                    <div className="mt-2">
                      <div className="font-medium text-red-600">Invalid symbols:</div>
                      <div className="text-red-600">{validationResults.invalid_symbols.join(', ')}</div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex space-x-3">
              <button
                onClick={validateSymbols}
                disabled={loading || symbols.length === 0}
                className="btn btn-secondary disabled:opacity-50"
              >
                {loading ? 'Validating...' : 'Validate Symbols'}
              </button>
              <button
                onClick={saveConfig}
                disabled={loading || symbols.length === 0}
                className="btn btn-primary disabled:opacity-50"
              >
                {loading ? 'Saving...' : 'Save Configuration'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Config
