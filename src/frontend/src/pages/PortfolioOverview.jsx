import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { portfolioApi } from '../services/api'
import { formatCurrency, formatPercent, getChangeColor } from '../utils/formatters'
import Chart from '../components/Chart'
import Loading from '../components/Loading'

function PortfolioOverview() {
  const [portfolio, setPortfolio] = useState(null)
  const [positions, setPositions] = useState([])
  const [chartData, setChartData] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        const [portfolioRes, positionsRes, chartRes] = await Promise.all([
          portfolioApi.getPortfolio(),
          portfolioApi.getPositions(),
          portfolioApi.getChart()
        ])
        
        setPortfolio(portfolioRes.data)
        setPositions(positionsRes.data.positions || [])
        
        // Transform chart data for lightweight-charts
        const transformedData = chartRes.data.history?.map(item => ({
          time: new Date(item.time * 1000).toISOString().split('T')[0], // Convert timestamp to YYYY-MM-DD
          value: item.value
        })) || []
        
        // Sort data by time and remove duplicates
        const sortedData = transformedData
          .sort((a, b) => new Date(a.time) - new Date(b.time))
          .filter((item, index, arr) => index === 0 || item.time !== arr[index - 1].time)
        
        setChartData(sortedData)
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  if (loading) return <Loading message="Loading portfolio..." />
  if (error) return <div className="text-danger">Error: {error}</div>

  return (
    <div className="space-y-6">
      {/* Portfolio Summary */}
      <div className="bg-white rounded-lg shadow p-6">
        <h1 className="text-2xl font-bold mb-4">Portfolio Overview</h1>
        
        {portfolio && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-gray-600">Total Value</p>
              <p className="text-2xl font-bold">{formatCurrency(portfolio.total_value_usd)}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Total Return</p>
              <p className={`text-xl font-semibold ${getChangeColor(portfolio.total_return_pct)}`}>
                {formatCurrency(portfolio.total_return_usd)} ({formatPercent(portfolio.total_return_pct)})
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Day Change</p>
              <p className={`text-lg font-semibold ${getChangeColor(portfolio.day_change_pct)}`}>
                {formatPercent(portfolio.day_change_pct)}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Total Invested</p>
              <p className="text-lg">{formatCurrency(portfolio.total_invested_usd)}</p>
            </div>
          </div>
        )}
      </div>

      {/* Portfolio Chart */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Portfolio Performance (1M)</h2>
        <Chart data={chartData} type="line" />
      </div>

      {/* Positions */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">Positions</h2>
          <Link
            to="/transactions/new"
            className="bg-primary text-white px-4 py-2 rounded-md text-sm hover:bg-blue-600"
          >
            Add Transaction
          </Link>
        </div>
        
        {positions.length === 0 ? (
          <p className="text-gray-600">No positions yet. Add your first transaction to get started.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2">Asset</th>
                  <th className="text-right py-2">Quantity</th>
                  <th className="text-right py-2">Avg Price</th>
                  <th className="text-right py-2">Current Price</th>
                  <th className="text-right py-2">Value</th>
                  <th className="text-right py-2">P&L</th>
                </tr>
              </thead>
              <tbody>
                {positions.map((position, index) => (
                  <tr key={`${position.symbol}-${index}`} className="border-b hover:bg-gray-50">
                    <td className="py-3">
                      <Link
                        to={`/assets/${position.asset_id}`}
                        className="text-primary hover:underline"
                      >
                        <div>
                          <p className="font-medium">{position.symbol}</p>
                          <p className="text-sm text-gray-600">{position.name}</p>
                        </div>
                      </Link>
                    </td>
                    <td className="text-right py-3">{position.quantity}</td>
                    <td className="text-right py-3">{formatCurrency(position.average_buy_price)}</td>
                    <td className="text-right py-3">{formatCurrency(position.current_price)}</td>
                    <td className="text-right py-3">{formatCurrency(position.current_value)}</td>
                    <td className={`text-right py-3 ${getChangeColor(position.unrealized_gain)}`}>
                      {formatCurrency(position.unrealized_gain)} ({formatPercent(position.unrealized_gain_pct)})
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

export default PortfolioOverview