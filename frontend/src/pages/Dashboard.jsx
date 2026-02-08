import React from 'react'
import RecommendationTable from '../components/RecommendationTable'
import PriceChart from '../components/PriceChart'
import { formatPrice, formatPercentage } from '../services/api'

const Dashboard = ({ recommendations, loading, onRefresh, systemHealth }) => {
  const summaryStats = {
    total: recommendations.length,
    strongBuy: recommendations.filter(r => r.recommendation === 'Strong Buy').length,
    buy: recommendations.filter(r => r.recommendation === 'Buy').length,
    hold: recommendations.filter(r => r.recommendation === 'Hold').length,
    sell: recommendations.filter(r => r.recommendation === 'Sell').length,
    strongSell: recommendations.filter(r => r.recommendation === 'Strong Sell').length,
    highConfidence: recommendations.filter(r => r.confidence_level === 'High').length,
    avgConfidence: recommendations.length > 0 
      ? recommendations.reduce((sum, r) => sum + (r.confidence_level === 'High' ? 3 : r.confidence_level === 'Medium' ? 2 : 1), 0) / recommendations.length
      : 0
  }

  const topRecommendations = recommendations.slice(0, 5)
  const avgScore = recommendations.length > 0 
    ? (recommendations.reduce((sum, r) => sum + (r.score || 0), 0) / recommendations.length).toFixed(1)
    : 0

  const getRecommendationIcon = (recommendation) => {
    switch (recommendation) {
      case 'Strong Buy':
        return '📈'
      case 'Buy':
        return '📊'
      case 'Hold':
        return '⏸️'
      case 'Sell':
        return '📉'
      case 'Strong Sell':
        return '⚠️'
      default:
        return '📋'
    }
  }

  const getConfidenceColor = (confidence) => {
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

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-6 sm:mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">🚀 7H Stock Analyzer</h1>
        <p className="mt-2 text-sm sm:text-base text-gray-600">
          AI-powered stock recommendations with technical analysis and real-time market data
        </p>
      </div>

      {/* System Health Banner */}
      {systemHealth && (
        <div className={`mb-4 sm:mb-6 p-3 sm:p-4 rounded-lg border ${
          systemHealth.status === 'healthy' 
            ? 'bg-green-50 border-green-200' 
            : 'bg-red-50 border-red-200'
        }`}>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-2 sm:space-y-0">
            <div className="flex items-center space-x-3">
              <span className={`text-xl sm:text-2xl ${systemHealth.status === 'healthy' ? 'text-green-600' : 'text-red-600'}`}>
                {systemHealth.status === 'healthy' ? '✅' : '❌'}
              </span>
              <div>
                <h3 className="font-semibold text-gray-900 text-sm sm:text-base">
                  System Status: {systemHealth.status === 'healthy' ? 'All Systems Operational' : 'System Issues Detected'}
                </h3>
                <p className="text-xs sm:text-sm text-gray-600">
                  Version: {systemHealth.version} | Region: {systemHealth.region || 'N/A'}
                </p>
              </div>
            </div>
            <div className="text-xs sm:text-sm text-gray-500">
              Last check: {new Date(systemHealth.timestamp).toLocaleString()}
            </div>
          </div>
        </div>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 sm:gap-6 mb-6 sm:mb-8">
        <div className="card bg-gradient-to-br from-blue-50 to-blue-100 border-l-4 border-blue-500 p-3 sm:p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 sm:w-10 sm:h-10 bg-blue-500 rounded-full flex items-center justify-center">
                <span className="text-white font-bold text-sm sm:text-base">📊</span>
              </div>
            </div>
            <div className="ml-2 sm:ml-4">
              <p className="text-xs sm:text-sm font-medium text-blue-600">Total Stocks</p>
              <p className="text-lg sm:text-2xl font-bold text-blue-900">{summaryStats.total}</p>
            </div>
          </div>
        </div>

        <div className="card bg-gradient-to-br from-green-50 to-green-100 border-l-4 border-green-500 p-3 sm:p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 sm:w-10 sm:h-10 bg-green-500 rounded-full flex items-center justify-center">
                <span className="text-white font-bold text-sm sm:text-base">📈</span>
              </div>
            </div>
            <div className="ml-2 sm:ml-4">
              <p className="text-xs sm:text-sm font-medium text-green-600">Buy Signals</p>
              <p className="text-lg sm:text-2xl font-bold text-green-900">
                {summaryStats.strongBuy + summaryStats.buy}
              </p>
            </div>
          </div>
        </div>

        <div className="card bg-gradient-to-br from-yellow-50 to-yellow-100 border-l-4 border-yellow-500 p-3 sm:p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 sm:w-10 sm:h-10 bg-yellow-500 rounded-full flex items-center justify-center">
                <span className="text-white font-bold text-sm sm:text-base">⏸️</span>
              </div>
            </div>
            <div className="ml-2 sm:ml-4">
              <p className="text-xs sm:text-sm font-medium text-yellow-600">Hold Signals</p>
              <p className="text-lg sm:text-2xl font-bold text-yellow-900">{summaryStats.hold}</p>
            </div>
          </div>
        </div>

        <div className="card bg-gradient-to-br from-red-50 to-red-100 border-l-4 border-red-500 p-3 sm:p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 sm:w-10 sm:h-10 bg-red-500 rounded-full flex items-center justify-center">
                <span className="text-white font-bold text-sm sm:text-base">📉</span>
              </div>
            </div>
            <div className="ml-2 sm:ml-4">
              <p className="text-xs sm:text-sm font-medium text-red-600">Sell Signals</p>
              <p className="text-lg sm:text-2xl font-bold text-red-900">
                {summaryStats.sell + summaryStats.strongSell}
              </p>
            </div>
          </div>
        </div>

        <div className="card bg-gradient-to-br from-purple-50 to-purple-100 border-l-4 border-purple-500 p-3 sm:p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 sm:w-10 sm:h-10 bg-purple-500 rounded-full flex items-center justify-center">
                <span className="text-white font-bold text-sm sm:text-base">⭐</span>
              </div>
            </div>
            <div className="ml-2 sm:ml-4">
              <p className="text-xs sm:text-sm font-medium text-purple-600">Avg Score</p>
              <p className="text-lg sm:text-2xl font-bold text-purple-900">{avgScore}</p>
            </div>
          </div>
        </div>

        <div className="card bg-gradient-to-br from-indigo-50 to-indigo-100 border-l-4 border-indigo-500 p-3 sm:p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 sm:w-10 sm:h-10 bg-indigo-500 rounded-full flex items-center justify-center">
                <span className="text-white font-bold text-sm sm:text-base">🎯</span>
              </div>
            </div>
            <div className="ml-2 sm:ml-4">
              <p className="text-xs sm:text-sm font-medium text-indigo-600">High Confidence</p>
              <p className="text-lg sm:text-2xl font-bold text-indigo-900">{summaryStats.highConfidence}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Top Recommendations */}
      <div className="mb-8">
        <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center mb-6 space-y-4 sm:space-y-0">
          <h2 className="text-xl sm:text-2xl font-bold text-gray-900">🏆 Top Recommendations</h2>
          <button
            onClick={onRefresh}
            disabled={loading}
            className="btn btn-primary disabled:opacity-50 flex items-center space-x-2 w-full sm:w-auto justify-center"
          >
            <span>{loading ? '🔄' : '🔄'}</span>
            <span>{loading ? 'Refreshing...' : 'Refresh'}</span>
          </button>
        </div>

        {loading ? (
          <div className="card">
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-4 border-blue-600"></div>
              <span className="ml-4 text-gray-600 text-lg">Analyzing stocks...</span>
            </div>
          </div>
        ) : recommendations.length === 0 ? (
          <div className="card">
            <div className="text-center py-12">
              <div className="text-gray-400 mb-4">
                <svg className="mx-auto h-16 w-16" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">No recommendations available</h3>
              <p className="text-gray-600 mb-6 max-w-md mx-auto">
                Start the stock analysis engine to get AI-powered recommendations based on technical indicators.
              </p>
              <button onClick={onRefresh} className="btn btn-primary text-lg px-6 py-3">
                🚀 Run Analysis
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {topRecommendations.map((rec, index) => (
              <div key={rec.symbol} className={`recommendation-card ${
                rec.recommendation === 'Strong Buy' || rec.recommendation === 'Buy' ? 'recommendation-buy' :
                rec.recommendation === 'Hold' ? 'recommendation-hold' : 'recommendation-sell'
              }`}>
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-col sm:flex-row sm:items-center space-y-2 sm:space-y-0 sm:space-x-4 mb-3">
                      <div className="flex items-center space-x-2">
                        <span className="text-xl sm:text-2xl font-bold text-gray-900">{rec.symbol}</span>
                        <span className="text-xl sm:text-2xl">{getRecommendationIcon(rec.recommendation)}</span>
                      </div>
                      <span className="text-gray-700 font-medium text-sm sm:text-base">{rec.company}</span>
                      <span className={`px-2 sm:px-3 py-1 text-xs sm:text-sm font-bold rounded-full ${
                        rec.recommendation === 'Strong Buy' ? 'bg-green-100 text-green-800 border border-green-300' :
                        rec.recommendation === 'Buy' ? 'bg-green-50 text-green-700 border border-green-200' :
                        rec.recommendation === 'Hold' ? 'bg-yellow-50 text-yellow-700 border border-yellow-200' :
                        rec.recommendation === 'Sell' ? 'bg-red-50 text-red-700 border border-red-200' :
                        'bg-red-100 text-red-800 border border-red-300'
                      }`}>
                        {rec.recommendation}
                      </span>
                      {rec.confidence_level && (
                        <span className={`px-2 py-1 text-xs font-medium rounded-full border ${getConfidenceColor(rec.confidence_level)}`}>
                          {rec.confidence_level} Confidence
                        </span>
                      )}
                      <div className="flex items-center space-x-1">
                        <span className="text-yellow-500 text-sm">{'⭐'.repeat(Math.min(Math.round(rec.score), 5))}</span>
                        <span className="text-gray-400 text-sm">{'☆'.repeat(Math.max(5 - Math.round(rec.score), 0))}</span>
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-7 gap-2 sm:gap-4 text-sm mb-3">
                      <div className="bg-white rounded-lg p-2 sm:p-3 border border-gray-200">
                        <div className="text-gray-600 text-xs mb-1">Current Price</div>
                        <div className="font-bold text-base sm:text-lg">{formatPrice(rec.price)}</div>
                        <div className={`text-xs font-medium ${rec.change_pct >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {formatPercentage(rec.change_pct)}
                        </div>
                      </div>
                      {rec.target_price && (
                        <div className="bg-white rounded-lg p-2 sm:p-3 border border-gray-200">
                          <div className="text-gray-600 text-xs mb-1">Target Price</div>
                          <div className="font-bold text-base sm:text-lg text-blue-600">{formatPrice(rec.target_price)}</div>
                          <div className="text-xs text-gray-500">
                            {rec.current_price ? ((rec.target_price - rec.current_price) / rec.current_price * 100).toFixed(1) : 'N/A'}% potential
                          </div>
                        </div>
                      )}
                      {rec.stop_loss && (
                        <div className="bg-white rounded-lg p-2 sm:p-3 border border-gray-200">
                          <div className="text-gray-600 text-xs mb-1">Stop Loss</div>
                          <div className="font-bold text-base sm:text-lg text-red-600">{formatPrice(rec.stop_loss)}</div>
                          <div className="text-xs text-gray-500">
                            {rec.current_price ? ((rec.current_price - rec.stop_loss) / rec.current_price * 100).toFixed(1) : 'N/A'}% risk
                          </div>
                        </div>
                      )}
                      <div className="bg-white rounded-lg p-2 sm:p-3 border border-gray-200">
                        <div className="text-gray-600 text-xs mb-1">RSI</div>
                        <div className="font-bold text-base sm:text-lg">{rec.rsi?.toFixed(1) || 'N/A'}</div>
                        <div className="text-xs text-gray-500">
                          {rec.rsi > 70 ? 'Overbought' : rec.rsi < 30 ? 'Oversold' : 'Neutral'}
                        </div>
                      </div>
                      <div className="bg-white rounded-lg p-2 sm:p-3 border border-gray-200">
                        <div className="text-gray-600 text-xs mb-1">MACD</div>
                        <div className="font-bold text-base sm:text-lg">{rec.macd?.toFixed(3) || 'N/A'}</div>
                        <div className="text-xs text-gray-500">
                          {rec.macd > 0 ? 'Bullish' : 'Bearish'}
                        </div>
                      </div>
                      <div className="bg-white rounded-lg p-2 sm:p-3 border border-gray-200">
                        <div className="text-gray-600 text-xs mb-1">Volume</div>
                        <div className="font-bold text-base sm:text-lg">
                          {rec.fundamental?.volume ? 
                            (rec.fundamental.volume / 1000000).toFixed(1) + 'M' : 'N/A'}
                        </div>
                        <div className="text-xs text-gray-500">shares</div>
                      </div>
                      <div className="bg-white rounded-lg p-2 sm:p-3 border border-gray-200">
                        <div className="text-gray-600 text-xs mb-1">Market Cap</div>
                        <div className="font-bold text-base sm:text-lg">
                          {rec.fundamental?.market_cap ? 
                            (rec.fundamental.market_cap / 1000000000).toFixed(1) + 'B' : 'N/A'}
                        </div>
                        <div className="text-xs text-gray-500">USD</div>
                      </div>
                    </div>
                    
                    {/* Technical Indicators */}
                    {rec.technical_indicators && rec.technical_indicators.length > 0 && (
                      <div className="mb-3">
                        <div className="flex flex-wrap gap-1">
                          {rec.technical_indicators.map((indicator, idx) => (
                            <span key={idx} className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full border border-blue-200">
                              {indicator}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {/* Price Chart */}
                    {rec.price_chart_url && (
                      <div className="mb-3">
                        <PriceChart symbol={rec.symbol} imageUrl={rec.price_chart_url} />
                      </div>
                    )}
                    
                    {rec.reasoning && (
                      <div className="bg-gray-50 rounded-lg p-3 border-l-4 border-blue-400">
                        <div className="flex items-start">
                          <span className="text-blue-500 mr-2">💡</span>
                          <div>
                            <span className="font-semibold text-gray-700">Analysis:</span>
                            <span className="text-gray-600 ml-2">{rec.reasoning}</span>
                          </div>
                        </div>
                      </div>
                    )}
                    
                    {/* Recon Data */}
                    {(rec.target_met || rec.stop_loss_hit || rec.days_to_target) && (
                      <div className={`rounded-lg p-3 border-l-4 ${
                        rec.target_met ? 'bg-green-50 border-green-400' :
                        rec.stop_loss_hit ? 'bg-red-50 border-red-400' :
                        'bg-blue-50 border-blue-400'
                      }`}>
                        <div className="flex items-start">
                          <span className={`mr-2 ${
                            rec.target_met ? 'text-green-500' :
                            rec.stop_loss_hit ? 'text-red-500' :
                            'text-blue-500'
                          }`}>
                            {rec.target_met ? '🎯' : rec.stop_loss_hit ? '🛑' : '⏱️'}
                          </span>
                          <div>
                            <span className="font-semibold text-gray-700">Status:</span>
                            <span className="text-gray-600 ml-2">
                              {rec.target_met ? `Target reached in ${rec.days_to_target} days` :
                               rec.stop_loss_hit ? `Stop loss hit after ${rec.days_to_target} days` :
                               `Active for ${rec.days_to_target} days`}
                            </span>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                  
                  <div className="ml-0 sm:ml-6 text-center flex-shrink-0">
                    <div className="text-2xl sm:text-3xl font-bold text-gray-900 mb-1">#{index + 1}</div>
                    <div className="text-xs sm:text-sm text-gray-600">Rank</div>
                    <div className="text-xs text-gray-500 mt-1">Score: {rec.score ? rec.score.toFixed(2) : 'N/A'}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Performance Summary */}
      {recommendations.length > 0 && (
        <div className="mb-8">
          <h2 className="text-xl sm:text-2xl font-bold text-gray-900 mb-6">📊 Performance Summary</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
            <div className="card p-4 sm:p-6">
              <h3 className="text-base sm:text-lg font-semibold text-gray-900 mb-4">Recommendation Distribution</h3>
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-xs sm:text-sm text-gray-600">Strong Buy</span>
                  <span className="font-bold text-green-600 text-sm sm:base">{summaryStats.strongBuy}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs sm:text-sm text-gray-600">Buy</span>
                  <span className="font-bold text-green-500 text-sm sm:base">{summaryStats.buy}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs sm:text-sm text-gray-600">Hold</span>
                  <span className="font-bold text-yellow-600 text-sm sm:base">{summaryStats.hold}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs sm:text-sm text-gray-600">Sell</span>
                  <span className="font-bold text-red-500 text-sm sm:base">{summaryStats.sell}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs sm:text-sm text-gray-600">Strong Sell</span>
                  <span className="font-bold text-red-600 text-sm sm:base">{summaryStats.strongSell}</span>
                </div>
              </div>
            </div>
            
            <div className="card p-4 sm:p-6">
              <h3 className="text-base sm:text-lg font-semibold text-gray-900 mb-4">Confidence Analysis</h3>
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-xs sm:text-sm text-gray-600">High Confidence</span>
                  <span className="font-bold text-green-600 text-sm sm:base">{summaryStats.highConfidence}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs sm:text-sm text-gray-600">Avg Confidence</span>
                  <span className="font-bold text-blue-600 text-sm sm:base">{summaryStats.avgConfidence ? summaryStats.avgConfidence.toFixed(1) : 'N/A'}/3.0</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs sm:text-sm text-gray-600">Total Analyzed</span>
                  <span className="font-bold text-gray-900 text-sm sm:base">{summaryStats.total}</span>
                </div>
              </div>
            </div>
            
            <div className="card p-4 sm:p-6">
              <h3 className="text-base sm:text-lg font-semibold text-gray-900 mb-4">Technical Indicators Used</h3>
              <div className="space-y-2">
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 sm:gap-4">
                  {['RSI', 'MACD', 'SMA_20', 'SMA_50', 'Bollinger_Bands', 'Volume_SMA'].map(indicator => {
                    const count = recommendations.filter(r => r.technical_indicators?.includes(indicator)).length
                    return (
                      <div key={indicator} className="flex items-center space-x-2">
                        <span className="text-xs sm:text-sm text-gray-600">{indicator}:</span>
                        <span className="font-bold text-blue-600 text-sm sm:base">{count}</span>
                      </div>
                    )
                  })}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Full Table */}
      {recommendations.length > 0 && (
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-gray-900 mb-6">📋 All Recommendations</h2>
          <div className="overflow-x-auto">
            <RecommendationTable recommendations={recommendations} />
          </div>
        </div>
      )}
    </div>
  )
}

export default Dashboard
