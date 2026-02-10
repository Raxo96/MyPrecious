import { useState, useEffect } from 'react'
import { Link, useParams, useNavigate } from 'react-router-dom'
import { portfolioApi } from '../services/api'
import { formatCurrency, formatPercent, getChangeColor } from '../utils/formatters'
import Chart from '../components/Chart'
import Loading from '../components/Loading'
import EditPortfolioModal from '../components/EditPortfolioModal'
import DeletePortfolioConfirmation from '../components/DeletePortfolioConfirmation'
import { useToast } from '../components/ToastContainer'

function PortfolioOverview() {
  const { id } = useParams()
  const navigate = useNavigate()
  const toast = useToast()
  const [portfolio, setPortfolio] = useState(null)
  const [positions, setPositions] = useState([])
  const [chartData, setChartData] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [isEditModalOpen, setIsEditModalOpen] = useState(false)
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false)

  const fetchData = async () => {
    try {
      setLoading(true)
      const [portfolioRes, positionsRes, chartRes] = await Promise.all([
        portfolioApi.getPortfolio(id),
        portfolioApi.getPositions(id),
        portfolioApi.getChart(id)
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

  useEffect(() => {
    if (id) {
      fetchData()
    }
  }, [id])

  const handleEditSuccess = () => {
    // Refresh portfolio data after successful edit
    fetchData()
    toast.success('Portfolio updated successfully!')
  }

  const handleDeleteSuccess = () => {
    // Navigate back to portfolio list after successful deletion
    toast.success('Portfolio deleted successfully!')
    navigate('/')
  }

  if (loading) return <Loading message="Loading portfolio..." />
  
  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-center">
          <div className="text-red-600 mb-4">
            <svg 
              className="mx-auto h-12 w-12 mb-3" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth={2} 
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" 
              />
            </svg>
            <p className="font-semibold text-lg">Error loading portfolio</p>
            <p className="text-sm mt-2 text-gray-600">{error}</p>
          </div>
          <div className="flex justify-center space-x-3">
            <button
              onClick={fetchData}
              className="bg-primary text-white px-6 py-2 rounded-md hover:bg-blue-600"
            >
              Retry
            </button>
            <Link
              to="/"
              className="bg-gray-200 text-gray-700 px-6 py-2 rounded-md hover:bg-gray-300"
            >
              Back to Portfolios
            </Link>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Back Navigation and Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div className="flex items-center space-x-2 sm:space-x-4">
          <Link
            to="/"
            className="text-gray-600 hover:text-gray-900 flex items-center text-sm sm:text-base"
          >
            <svg 
              className="w-4 h-4 sm:w-5 sm:h-5 mr-1" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth={2} 
                d="M15 19l-7-7 7-7" 
              />
            </svg>
            <span className="hidden sm:inline">Back to Portfolios</span>
            <span className="sm:hidden">Back</span>
          </Link>
          {portfolio && (
            <h1 className="text-xl sm:text-2xl font-bold truncate">{portfolio.name}</h1>
          )}
        </div>
        
        {/* Action Buttons */}
        <div className="flex space-x-2">
          <button
            onClick={() => setIsEditModalOpen(true)}
            className="px-3 py-2 text-xs sm:text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
          >
            Edit
          </button>
          <button
            onClick={() => setIsDeleteModalOpen(true)}
            className="px-3 py-2 text-xs sm:text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700 transition-colors"
          >
            Delete
          </button>
        </div>
      </div>

      {/* Portfolio Summary */}
      <div className="bg-white rounded-lg shadow p-4 md:p-6">
        <h2 className="text-lg md:text-xl font-semibold mb-3 md:mb-4">Portfolio Overview</h2>
        
        {portfolio && (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4">
            <div>
              <p className="text-xs md:text-sm text-gray-600">Total Value</p>
              <p className="text-lg md:text-2xl font-bold">{formatCurrency(portfolio.total_value_usd)}</p>
            </div>
            <div>
              <p className="text-xs md:text-sm text-gray-600">Total Return</p>
              <p className={`text-sm md:text-xl font-semibold ${getChangeColor(portfolio.total_return_pct)}`}>
                {formatCurrency(portfolio.total_return_usd)} ({formatPercent(portfolio.total_return_pct)})
              </p>
            </div>
            <div>
              <p className="text-xs md:text-sm text-gray-600">Day Change</p>
              <p className={`text-sm md:text-lg font-semibold ${getChangeColor(portfolio.day_change_pct)}`}>
                {formatPercent(portfolio.day_change_pct)}
              </p>
            </div>
            <div>
              <p className="text-xs md:text-sm text-gray-600">Total Invested</p>
              <p className="text-sm md:text-lg">{formatCurrency(portfolio.total_invested_usd)}</p>
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
      <div className="bg-white rounded-lg shadow p-4 md:p-6">
        <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center mb-4 gap-3">
          <h2 className="text-lg md:text-xl font-semibold">Positions</h2>
          <Link
            to={`/transactions/new?portfolio_id=${id}`}
            className="bg-primary text-white px-4 py-2 rounded-md text-sm hover:bg-blue-600 text-center transition-colors"
          >
            Add Transaction
          </Link>
        </div>
        
        {positions.length === 0 ? (
          <p className="text-gray-600 text-sm md:text-base">No positions yet. Add your first transaction to get started.</p>
        ) : (
          <div className="overflow-x-auto -mx-4 md:mx-0">
            <div className="inline-block min-w-full align-middle">
              <table className="min-w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2 px-2 md:px-0 text-xs md:text-sm">Asset</th>
                    <th className="text-right py-2 px-2 text-xs md:text-sm">Qty</th>
                    <th className="text-right py-2 px-2 text-xs md:text-sm hidden sm:table-cell">Avg Price</th>
                    <th className="text-right py-2 px-2 text-xs md:text-sm">Price</th>
                    <th className="text-right py-2 px-2 text-xs md:text-sm">Value</th>
                    <th className="text-right py-2 px-2 md:px-0 text-xs md:text-sm">P&L</th>
                  </tr>
                </thead>
                <tbody>
                  {positions.map((position, index) => (
                    <tr key={`${position.symbol}-${index}`} className="border-b hover:bg-gray-50">
                      <td className="py-3 px-2 md:px-0">
                        <Link
                          to={`/assets/${position.symbol}`}
                          className="text-primary hover:underline"
                        >
                          <div>
                            <p className="font-medium text-xs md:text-base">{position.symbol}</p>
                            <p className="text-xs text-gray-600 hidden md:block">{position.name}</p>
                          </div>
                        </Link>
                      </td>
                      <td className="text-right py-3 px-2 text-xs md:text-base">{position.quantity}</td>
                      <td className="text-right py-3 px-2 text-xs md:text-base hidden sm:table-cell">{formatCurrency(position.average_buy_price)}</td>
                      <td className="text-right py-3 px-2 text-xs md:text-base">{formatCurrency(position.current_price)}</td>
                      <td className="text-right py-3 px-2 text-xs md:text-base">{formatCurrency(position.current_value)}</td>
                      <td className={`text-right py-3 px-2 md:px-0 text-xs md:text-base ${getChangeColor(position.unrealized_gain)}`}>
                        <div className="flex flex-col items-end">
                          <span>{formatCurrency(position.unrealized_gain)}</span>
                          <span className="text-xs">({formatPercent(position.unrealized_gain_pct)})</span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Edit Portfolio Modal */}
      <EditPortfolioModal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        onSuccess={handleEditSuccess}
        portfolio={portfolio}
      />

      {/* Delete Portfolio Confirmation */}
      <DeletePortfolioConfirmation
        isOpen={isDeleteModalOpen}
        onClose={() => setIsDeleteModalOpen(false)}
        onSuccess={handleDeleteSuccess}
        portfolio={portfolio}
      />
    </div>
  )
}

export default PortfolioOverview