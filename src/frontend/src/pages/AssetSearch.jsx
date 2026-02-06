import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { assetApi } from '../services/api'
import { formatCurrency, formatPercent, getChangeColor } from '../utils/formatters'
import Loading from '../components/Loading'

function AssetSearch() {
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [assets, setAssets] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  
  // State for all assets table
  const [allAssets, setAllAssets] = useState([])
  const [loadingAll, setLoadingAll] = useState(false)
  const [errorAll, setErrorAll] = useState(null)

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

  const fetchAllAssets = async () => {
    try {
      setLoadingAll(true)
      setErrorAll(null)
      const response = await assetApi.getAll()
      setAllAssets(response.data.assets || [])
    } catch (err) {
      setErrorAll(err.message)
      setAllAssets([])
    } finally {
      setLoadingAll(false)
    }
  }

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      searchAssets(query)
    }, 300) // Debounce search

    return () => clearTimeout(timeoutId)
  }, [query])

  useEffect(() => {
    fetchAllAssets()
  }, [])

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

        {/* Assets Table - shown when no search query */}
        {!query && loadingAll && <Loading message="Loading assets..." />}
        
        {!query && errorAll && (
          <div className="text-danger bg-red-50 p-4 rounded-md">
            Error: {errorAll}
          </div>
        )}

        {!query && !loadingAll && !errorAll && allAssets.length === 0 && (
          <p className="text-gray-600">No assets available</p>
        )}

        {!query && !loadingAll && !errorAll && allAssets.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="border-b-2 border-gray-300">
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">Asset Name</th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">Symbol</th>
                  <th className="text-right py-3 px-4 font-semibold text-gray-700">Current Price</th>
                  <th className="text-right py-3 px-4 font-semibold text-gray-700">1D Change %</th>
                </tr>
              </thead>
              <tbody>
                {allAssets.map((asset) => (
                  <tr
                    key={asset.id}
                    onClick={() => navigate(`/assets/${asset.symbol}`)}
                    className="border-b border-gray-200 hover:bg-gray-50 cursor-pointer transition-colors"
                  >
                    <td className="py-3 px-4">{asset.name}</td>
                    <td className="py-3 px-4 font-medium">{asset.symbol}</td>
                    <td className="py-3 px-4 text-right font-medium">{formatCurrency(asset.current_price)}</td>
                    <td className={`py-3 px-4 text-right font-medium ${getChangeColor(asset.day_change_pct)}`}>
                      {formatPercent(asset.day_change_pct)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Search Results - shown when there's a search query */}
        {query && assets.length > 0 && (
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