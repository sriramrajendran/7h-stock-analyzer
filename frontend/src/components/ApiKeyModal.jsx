import React, { useState, useEffect } from 'react'

const ApiKeyModal = ({ isOpen, onClose, onApiKeySet }) => {
  const [apiKey, setApiKey] = useState('')
  const [showKey, setShowKey] = useState(false)
  const [rememberKey, setRememberKey] = useState(false)

  // Load saved key on mount
  useEffect(() => {
    const savedKey = localStorage.getItem('stockAnalyzerApiKey')
    if (savedKey) {
      setApiKey(savedKey)
      setRememberKey(true)
      onApiKeySet(savedKey)
    }
  }, [onApiKeySet])

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!apiKey.trim()) return

    // Save to localStorage if user wants to remember
    if (rememberKey) {
      localStorage.setItem('stockAnalyzerApiKey', apiKey.trim())
    } else {
      localStorage.removeItem('stockAnalyzerApiKey')
    }

    onApiKeySet(apiKey.trim())
    onClose()
  }

  const handleClear = () => {
    setApiKey('')
    setRememberKey(false)
    localStorage.removeItem('stockAnalyzerApiKey')
    onApiKeySet('')
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold text-gray-900">API Key Required</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            ✕
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="apiKey" className="block text-sm font-medium text-gray-700 mb-1">
              API Key
            </label>
            <div className="relative">
              <input
                id="apiKey"
                type={showKey ? 'text' : 'password'}
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="Enter your API key"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                required
              />
              <button
                type="button"
                onClick={() => setShowKey(!showKey)}
                className="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                {showKey ? '👁️' : '👁️‍🗨️'}
              </button>
            </div>
            <p className="mt-1 text-xs text-gray-500">
              Your API key is stored only in your browser and never sent to any server.
            </p>
          </div>

          <div className="flex items-center">
            <input
              id="rememberKey"
              type="checkbox"
              checked={rememberKey}
              onChange={(e) => setRememberKey(e.target.checked)}
              className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
            />
            <label htmlFor="rememberKey" className="ml-2 block text-sm text-gray-700">
              Remember API key in browser
            </label>
          </div>

          <div className="flex space-x-3 pt-2">
            <button
              type="submit"
              className="flex-1 bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
            >
              Set API Key
            </button>
            <button
              type="button"
              onClick={handleClear}
              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
            >
              Clear
            </button>
          </div>
        </form>

        <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
          <p className="text-sm text-blue-800">
            <strong>Security Note:</strong> Your API key is stored locally in your browser only. 
            Clear your browser data to remove it. Never share your API key.
          </p>
        </div>
      </div>
    </div>
  )
}

export default ApiKeyModal
