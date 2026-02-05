import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { assetApi } from '../services/api'
import { formatCurrency, formatPercent, getChangeColor } from '../utils/formatters'
import Chart from '../components/Chart'
import Loading from '../components/Loading'

function AssetDetail() {
  const { id } = useParams()
  const [asset, setAsset] = useState(null)
  const [chartData, setChartData] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchAssetData = async () => {
      try {
        setLoading(true)
        const [assetRes, chartRes] = await Promise.all([
          assetApi.getAsset(id),
          assetApi.getChart(id)
        ])
        
        setAsset(assetRes.data)
        
        // Transform chart data for candlestick chart
        const transformedData = chartRes.data.data?.map(item => ({
          time: item.timestamp.split('T')[0], // Convert to YYYY-MM-DD format
          open: item.open,
          high: item.high,
          low: item.low,
          close: item.close
        })) || []
        setChartData(transformedData)
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    fetchAssetData()
  }, [id])

  if (loading) return <Loading message="Loading asset details..." />
  if (error) return <div className="text-danger">Error: {error}</div>
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