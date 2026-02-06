import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { assetApi } from '../services/api'
import { formatCurrency, formatPercent, getChangeColor } from '../utils/formatters'
import Chart from '../components/Chart'
import PriceChangeTable from '../components/PriceChangeTable'
import Loading from '../components/Loading'

function AssetDetail() {
  const { symbol } = useParams()
  const [asset, setAsset] = useState(null)
  const [chartData, setChartData] = useState([])
  const [priceChanges, setPriceChanges] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchAssetData = async () => {
    try {
      setLoading(true)
      setError(null)
      const [assetRes, chartRes] = await Promise.all([
        assetApi.getAsset(symbol),
        assetApi.getChart(symbol)
      ])
      
      setAsset(assetRes.data)
      
      // Extract price changes from chart response
      if (chartRes.data && chartRes.data.price_changes) {
        setPriceChanges(chartRes.data.price_changes)
      }
      
      // Transform chart data for candlestick chart (if available)
      const transformedData = chartRes.data.data?.map(item => ({
        time: item.timestamp.split('T')[0], // Convert to YYYY-MM-DD format
        open: item.open,
        high: item.high,
        low: item.low,
        close: item.close
      })) || []
      setChartData(transformedData)
    } catch (err) {
      // Check if it's a 404 error
      if (err.response && err.response.status === 404) {
        setError('notFound')
      } else if (!err.response) {
        // Network error (no response from server)
        setError('network')
      } else {
        // Other errors
        setError(err.message || 'An error occurred while loading the asset')
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAssetData()
  }, [symbol])

  if (loading) return <Loading message="Loading asset details..." />
  
  // Handle 404 error with user-friendly message
  if (error === 'notFound') {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] space-y-4">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">Asset Not Found</h1>
          <p className="text-lg text-gray-600 mb-6">
            The asset "{symbol}" could not be found in our database.
          </p>
          <Link
            to="/assets"
            className="inline-block bg-primary text-white px-6 py-3 rounded-md hover:bg-blue-600 transition-colors"
          >
            ← Back to Asset Search
          </Link>
        </div>
      </div>
    )
  }
  
  // Handle network errors with retry option
  if (error === 'network') {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] space-y-4">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-red-600 mb-2">Network Error</h1>
          <p className="text-gray-600 mb-6">
            Unable to connect to the server. Please check your internet connection and try again.
          </p>
          <div className="flex gap-4 justify-center">
            <button
              onClick={fetchAssetData}
              className="bg-primary text-white px-6 py-3 rounded-md hover:bg-blue-600 transition-colors"
            >
              Retry
            </button>
            <Link
              to="/assets"
              className="inline-block bg-gray-500 text-white px-6 py-3 rounded-md hover:bg-gray-600 transition-colors"
            >
              ← Back to Asset Search
            </Link>
          </div>
        </div>
      </div>
    )
  }
  
  // Handle other errors
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] space-y-4">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-red-600 mb-2">Error</h1>
          <p className="text-gray-600 mb-6">{error}</p>
          <div className="flex gap-4 justify-center">
            <button
              onClick={fetchAssetData}
              className="bg-primary text-white px-6 py-3 rounded-md hover:bg-blue-600 transition-colors"
            >
              Retry
            </button>
            <Link
              to="/assets"
              className="inline-block bg-gray-500 text-white px-6 py-3 rounded-md hover:bg-gray-600 transition-colors"
            >
              ← Back to Asset Search
            </Link>
          </div>
        </div>
      </div>
    )
  }
  
  if (!asset) return <div>Asset not found</div>

  return (
    <div className="space-y-6">
      {/* Asset Header */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h1 className="text-3xl font-bold">{asset.symbol}</h1>
            <p className="text-xl text-gray-600">{asset.name}</p>
            <p className="text-sm text-gray-500">
              {asset.asset_type} • {asset.exchange} • {asset.native_currency}
            </p>
          </div>
          <Link
            to={`/transactions/new?asset_id=${asset.id}`}
            className="bg-primary text-white px-4 py-2 rounded-md hover:bg-blue-600"
          >
            Add to Portfolio
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-gray-600">Current Price</p>
            <p className="text-2xl font-bold">{formatCurrency(asset.current_price)}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Day Change</p>
            <p className={`text-xl font-semibold ${getChangeColor(asset.day_change_pct)}`}>
              {formatPercent(asset.day_change_pct)}
            </p>
          </div>
          {asset.volume && (
            <div>
              <p className="text-sm text-gray-600">Volume</p>
              <p className="text-lg">{asset.volume.toLocaleString()}</p>
            </div>
          )}
          {asset.market_cap && (
            <div>
              <p className="text-sm text-gray-600">Market Cap</p>
              <p className="text-lg">{formatCurrency(asset.market_cap)}</p>
            </div>
          )}
        </div>
      </div>

      {/* Price Changes Table */}
      {priceChanges && <PriceChangeTable priceChanges={priceChanges} />}

      {/* Price Chart */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Price Chart (1M)</h2>
        {chartData.length > 0 ? (
          <Chart data={chartData} type="candlestick" />
        ) : (
          <div className="h-[300px] flex items-center justify-center text-gray-500">
            <p>Chart data not available</p>
          </div>
        )}
      </div>

      {/* Back to Search */}
      <div className="text-center">
        <Link
          to="/assets"
          className="text-primary hover:underline"
        >
          ← Back to Asset Search
        </Link>
      </div>
    </div>
  )
}

export default AssetDetail