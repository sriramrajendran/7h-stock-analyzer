import React, { useState } from 'react'
import { formatPrice, formatPercentage, getRecommendationBadgeColor } from '../services/api'

const RecommendationTable = ({ recommendations }) => {
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
        return '📋'
    }
  }

  return (
    <div className="card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gradient-to-r from-gray-50 to-gray-100">
            <tr>
              <th
                onClick={() => handleSort('symbol')}
                className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider cursor-pointer hover:bg-gray-200 transition-colors"
              >
                <div className="flex items-center space-x-1">
                  <span>Symbol</span>
                  {getSortIcon('symbol')}
                </div>
              </th>
              <th
                onClick={() => handleSort('company')}
                className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider cursor-pointer hover:bg-gray-200 transition-colors"
              >
                <div className="flex items-center space-x-1">
                  <span>Company</span>
                  {getSortIcon('company')}
                </div>
              </th>
              <th
                onClick={() => handleSort('price')}
                className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider cursor-pointer hover:bg-gray-200 transition-colors"
              >
                <div className="flex items-center space-x-1">
                  <span>Price</span>
                  {getSortIcon('price')}
                </div>
              </th>
              <th
                onClick={() => handleSort('change_pct')}
                className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider cursor-pointer hover:bg-gray-200 transition-colors"
              >
                <div className="flex items-center space-x-1">
                  <span>Change</span>
                  {getSortIcon('change_pct')}
                </div>
              </th>
              <th
                onClick={() => handleSort('target_price')}
                className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider cursor-pointer hover:bg-gray-200 transition-colors"
              >
                <div className="flex items-center space-x-1">
                  <span>Target</span>
                  {getSortIcon('target_price')}
                </div>
              </th>
              <th
                onClick={() => handleSort('stop_loss')}
                className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider cursor-pointer hover:bg-gray-200 transition-colors"
              >
                <div className="flex items-center space-x-1">
                  <span>Stop Loss</span>
                  {getSortIcon('stop_loss')}
                </div>
              </th>
              <th
                onClick={() => handleSort('recommendation')}
                className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider cursor-pointer hover:bg-gray-200 transition-colors"
              >
                <div className="flex items-center space-x-1">
                  <span>Signal</span>
                  {getSortIcon('recommendation')}
                </div>
              </th>
              <th
                onClick={() => handleSort('score')}
                className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider cursor-pointer hover:bg-gray-200 transition-colors"
              >
                <div className="flex items-center space-x-1">
                  <span>Score</span>
                  {getSortIcon('score')}
                </div>
              </th>
              <th className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">
                Analysis
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-100">
            {sortedRecommendations.map((rec, index) => (
              <tr key={rec.symbol} className="hover:bg-gray-50 transition-colors">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <div className="text-lg font-bold text-gray-900">{rec.symbol}</div>
                    <div className="ml-2 text-lg">{getRecommendationIcon(rec.recommendation)}</div>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <div className="text-sm text-gray-900 font-medium">{rec.company}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm">
                    <div className="font-bold text-gray-900">{formatPrice(rec.price)}</div>
                    <div className={`text-xs font-medium ${rec.change_pct >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {formatPercentage(rec.change_pct)}
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm">
                    <div className="font-bold text-blue-600">{formatPrice(rec.target_price)}</div>
                    <div className="text-xs text-gray-500">
                      +{((rec.target_price - rec.price) / rec.price * 100).toFixed(1)}%
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm">
                    <div className="font-bold text-red-600">{formatPrice(rec.stop_loss)}</div>
                    <div className="text-xs text-gray-500">
                      -{((rec.price - rec.stop_loss) / rec.price * 100).toFixed(1)}%
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-3 py-1 inline-flex text-xs leading-5 font-bold rounded-full border ${getRecommendationBadgeColor(rec.recommendation)}`}>
                    <span className="mr-1">{getRecommendationIcon(rec.recommendation)}</span>
                    {rec.recommendation.replace('_', ' ')}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <div className="text-sm text-gray-900 font-bold">{rec.score}</div>
                    <div className="ml-1 flex">
                      <span className="text-yellow-500 text-xs">{'⭐'.repeat(Math.min(rec.score, 5))}</span>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <div className="text-sm text-gray-600 max-w-xs">
                    <div className="truncate" title={rec.reasoning}>
                      {rec.reasoning}
                    </div>
                    {rec.rsi && (
                      <div className="text-xs text-gray-500 mt-1">
                        RSI: {rec.rsi.toFixed(1)}
                      </div>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      {recommendations.length === 0 && (
        <div className="text-center py-8">
          <div className="text-gray-400">
            <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
            </svg>
          </div>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No recommendations</h3>
          <p className="mt-1 text-sm text-gray-500">No stock recommendations available at this time.</p>
        </div>
      )}
    </div>
  )
}

export default RecommendationTable
