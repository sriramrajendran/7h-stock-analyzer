import React, { useState } from 'react'
import { formatPrice, formatPercentage, getRecommendationBadgeColor } from '../services/api'

const EnhancedRecommendationTable = ({ recommendations }) => {
  const [sortConfig, setSortConfig] = useState({ key: 'score', direction: 'descending' })

  const handleSort = (key) => {
    let direction = 'ascending'
    if (sortConfig.key === key && sortConfig.direction === 'ascending') {
      direction = 'descending'
    }
    setSortConfig({ key, direction })
  }

  const sortedRecommendations = React.useMemo(() => {
    const sortableRecommendations = [...recommendations]
    if (sortConfig.key !== null) {
      sortableRecommendations.sort((a, b) => {
        if (a[sortConfig.key] < b[sortConfig.key]) {
          return sortConfig.direction === 'ascending' ? -1 : 1
        }
        if (a[sortConfig.key] > b[sortConfig.key]) {
          return sortConfig.direction === 'ascending' ? 1 : -1
        }
        return 0
      })
    }
    return sortableRecommendations
  }, [recommendations, sortConfig])

  const getSortIcon = (key) => {
    if (sortConfig.key !== key) {
      return <span className="text-gray-400">↕️</span>
    }
    return sortConfig.direction === 'ascending' ? <span className="text-blue-600">🔼</span> : <span className="text-blue-600">🔽</span>
  }

  const getRecommendationIcon = (recommendation) => {
    switch (recommendation) {
      case 'STRONG_BUY':
        return '📈'
      case 'BUY':
        return '📊'
      case 'HOLD':
        return '⏸️'
      case 'SELL':
        return '📉'
      case 'STRONG_SELL':
        return '⚠️'
      default:
        return '📊'
    }
  }

  const getResultStatusBadge = (status) => {
    switch (status) {
      case 'target_met':
        return <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">✅ Target Met</span>
      case 'stop_loss_hit':
        return <span className="px-2 py-1 text-xs font-medium bg-red-100 text-red-800 rounded-full">❌ Stop Loss</span>
      case 'in_transit':
        return <span className="px-2 py-1 text-xs font-medium bg-yellow-100 text-yellow-800 rounded-full">⏳ In Transit</span>
      default:
        return <span className="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-800 rounded-full">❓ Unknown</span>
    }
  }

  const getPerformanceColor = (resultStatus) => {
    switch (resultStatus) {
      case 'target_met':
        return 'text-green-600'
      case 'stop_loss_hit':
        return 'text-red-600'
      case 'in_transit':
        return 'text-yellow-600'
      default:
        return 'text-gray-600'
    }
  }

  if (!recommendations || recommendations.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No recommendations available
      </div>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th 
              scope="col" 
              className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
              onClick={() => handleSort('symbol')}
            >
              Symbol {getSortIcon('symbol')}
            </th>
            <th 
              scope="col" 
              className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
              onClick={() => handleSort('recommendation')}
            >
              Recommendation {getSortIcon('recommendation')}
            </th>
            <th 
              scope="col" 
              className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
              onClick={() => handleSort('price')}
            >
              Current Price {getSortIcon('price')}
            </th>
            <th 
              scope="col" 
              className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
              onClick={() => handleSort('target_price')}
            >
              Target Price {getSortIcon('target_price')}
            </th>
            <th 
              scope="col" 
              className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
              onClick={() => handleSort('stop_loss')}
            >
              Stop Loss {getSortIcon('stop_loss')}
            </th>
            <th 
              scope="col" 
              className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
            >
              Result Status
            </th>
            <th 
              scope="col" 
              className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
              onClick={() => handleSort('days_to_target_result')}
            >
              Days to Target {getSortIcon('days_to_target_result')}
            </th>
            <th 
              scope="col" 
              className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
              onClick={() => handleSort('score')}
            >
              Score {getSortIcon('score')}
            </th>
            <th 
              scope="col" 
              className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
            >
              Confidence
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {sortedRecommendations.map((rec, index) => (
            <tr key={rec.symbol} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="flex items-center">
                  <div className="text-sm font-medium text-gray-900">{rec.symbol}</div>
                  {rec.company && (
                    <div className="text-sm text-gray-500">{rec.company}</div>
                  )}
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="flex items-center">
                  <span className="mr-2">{getRecommendationIcon(rec.recommendation)}</span>
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${getRecommendationBadgeColor(rec.recommendation)}`}>
                    {rec.recommendation.replace('_', ' ')}
                  </span>
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="text-sm text-gray-900">
                  {formatPrice(rec.recon_current_price || rec.price)}
                </div>
                {rec.change_pct && (
                  <div className={`text-sm ${rec.change_pct >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {formatPercentage(rec.change_pct)}
                  </div>
                )}
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="text-sm text-gray-900">
                  {formatPrice(rec.target_price)}
                </div>
                {rec.target_price && rec.recon_current_price && (
                  <div className="text-sm text-blue-600">
                    {formatPercentage(((rec.target_price - rec.recon_current_price) / rec.recon_current_price) * 100)}
                  </div>
                )}
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="text-sm text-gray-900">
                  {formatPrice(rec.stop_loss)}
                </div>
                {rec.stop_loss && rec.recon_current_price && (
                  <div className="text-sm text-red-600">
                    {formatPercentage(((rec.stop_loss - rec.recon_current_price) / rec.recon_current_price) * 100)}
                  </div>
                )}
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                {getResultStatusBadge(rec.result_status)}
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <div className={`text-sm font-medium ${getPerformanceColor(rec.result_status)}`}>
                  {rec.days_to_target_result !== null ? (
                    <span>{rec.days_to_target_result} days</span>
                  ) : (
                    <span className="text-gray-400">-</span>
                  )}
                </div>
                {rec.recon_days_elapsed > 0 && (
                  <div className="text-xs text-gray-500">
                    ({rec.recon_days_elapsed} days elapsed)
                  </div>
                )}
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="text-sm text-gray-900">
                  {rec.score?.toFixed(2) || '0.00'}
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                  rec.confidence_level === 'High' ? 'bg-green-100 text-green-800' :
                  rec.confidence_level === 'Medium' ? 'bg-yellow-100 text-yellow-800' :
                  'bg-gray-100 text-gray-800'
                }`}>
                  {rec.confidence_level || 'Low'}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default EnhancedRecommendationTable
