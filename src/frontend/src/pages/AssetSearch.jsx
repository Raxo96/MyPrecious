import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { assetApi } from '../services/api'
import { formatCurrency, formatPercent, getChangeColor } from '../utils/formatters'
import Loading from '../components/Loading'

function AssetSearch() {
  const [query, setQuery] = useState('')
  const [assets, setAssets] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const searchAssets = async (searchQuery) => {
    if (!searchQuery.trim()) {
      setAssets([])
      return
    }

    try {
      setLoading(true)
      setError(null)
      const response = await assetApi.search(searchQuery)
      setAssets(response.data.assets || [])
    } catch (err) {
      setError(err.message)
      setAssets([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      searchAssets(query)
    }, 300) // Debounce search

    return () => clearTimeout(timeoutId)
  }, [query])

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h1 className="text-2xl font-bold mb-4">Search Assets</h1>
        
        <div className="mb-6">
          <input
            type="text"
            placeholder="Search by symbol or name (e.g., AAPL, Apple)"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary focus:border-transparent"
          />
        </div>

        {loading && <Loading message="Searching assets..." />}
        
        {error && (
          <div className="text-danger bg-red-50 p-4 rounded-md">
            Error: {error}
          </div>
        )}

        {!loading && !error && assets.length === 0 && query && (
          <p className="text-gray-600">No assets found for "{query}"</p>
        )}

        {!loading && !error && query === '' && (
          <p className="text-gray-600">Enter a search term to find assets</p>
        )}

        {assets.length > 0 && (
          <div className="grid gap-4">
            {assets.map((asset) => (
              <Link
                key={asset.id}
                to={`/assets/${asset.symbol}`}
                className="block p-4 border border-gray-200 rounded-lg hover:border-primary hover:shadow-md transition-all"
              >
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-semibold text-lg">{asset.symbol}</h3>
                    <p className="text-gray-600">{asset.name}</p>
                    <p className="text-sm text-gray-500">
                      {asset.asset_type} • {asset.exchange}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold">{formatCurrency(asset.current_price)}</p>
                    <p className={`text-sm ${getChangeColor(asset.day_change_pct)}`}>
                      {formatPercent(asset.day_change_pct)}
                    </p>
                    {asset.is_tracked && (
                      <span className="inline-block mt-1 px-2 py-1 bg-green-100 text-green-800 text-xs rounded">
                        Tracked
                      </span>
                    )}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default AssetSearch