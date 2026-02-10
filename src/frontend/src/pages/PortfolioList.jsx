import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { portfolioApi } from '../services/api'
import { formatCurrency, formatPercent, getChangeColor } from '../utils/formatters'
import Loading from '../components/Loading'
import CreatePortfolioModal from '../components/CreatePortfolioModal'
import { useToast } from '../components/ToastContainer'

function PortfolioList() {
  const [portfolios, setPortfolios] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const navigate = useNavigate()
  const toast = useToast()

  useEffect(() => {
    fetchPortfolios()
  }, [])

  const fetchPortfolios = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await portfolioApi.getAll()
      const portfoliosList = response.data.portfolios || []
      
      // If no portfolios exist, automatically create "My Portfolio"
      if (portfoliosList.length === 0) {
        await createDefaultPortfolio()
        // Fetch portfolios again after creating the default one
        const refreshedResponse = await portfolioApi.getAll()
        setPortfolios(refreshedResponse.data.portfolios || [])
      } else {
        setPortfolios(portfoliosList)
      }
    } catch (err) {
      setError(err.message || 'Failed to load portfolios')
    } finally {
      setLoading(false)
    }
  }

  const createDefaultPortfolio = async () => {
    try {
      await portfolioApi.create({
        name: 'My Portfolio',
        currency: 'USD'
      })
    } catch (err) {
      console.error('Failed to create default portfolio:', err)
      // Don't throw - let the user create manually if auto-creation fails
    }
  }

  const handlePortfolioClick = (portfolioId) => {
    navigate(`/portfolios/${portfolioId}`)
  }

  const handleCreatePortfolio = () => {
    setIsCreateModalOpen(true)
  }

  const handleModalClose = () => {
    setIsCreateModalOpen(false)
  }

  const handleModalSuccess = () => {
    // Refresh the portfolio list after successful creation
    fetchPortfolios()
    toast.success('Portfolio created successfully!')
  }

  if (loading) return <Loading message="Loading portfolios..." />

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-danger">
          <p className="font-semibold">Error loading portfolios</p>
          <p className="text-sm mt-2">{error}</p>
          <button
            onClick={fetchPortfolios}
            className="mt-4 bg-primary text-white px-4 py-2 rounded-md text-sm hover:bg-blue-600"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  // Empty state
  if (portfolios.length === 0) {
    return (
      <>
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <div className="max-w-md mx-auto">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            <h3 className="mt-4 text-lg font-medium text-gray-900">No portfolios yet</h3>
            <p className="mt-2 text-sm text-gray-600">
              Get started by creating your first portfolio to track your investments.
            </p>
            <button
              onClick={handleCreatePortfolio}
              className="mt-6 bg-primary text-white px-6 py-3 rounded-md hover:bg-blue-600 font-medium"
            >
              Create Your First Portfolio
            </button>
          </div>
        </div>

        {/* Create Portfolio Modal */}
        <CreatePortfolioModal
          isOpen={isCreateModalOpen}
          onClose={handleModalClose}
          onSuccess={handleModalSuccess}
        />
      </>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">My Portfolios</h1>
        <button
          onClick={handleCreatePortfolio}
          className="bg-primary text-white px-4 py-2 rounded-md text-sm hover:bg-blue-600"
        >
          Create Portfolio
        </button>
      </div>

      {/* Portfolio Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
        {portfolios.map((portfolio) => (
          <div
            key={portfolio.id}
            onClick={() => handlePortfolioClick(portfolio.id)}
            className="bg-white rounded-lg shadow p-4 md:p-6 cursor-pointer hover:shadow-lg transition-all transform hover:-translate-y-1"
          >
            {/* Portfolio Name */}
            <h2 className="text-lg md:text-xl font-semibold mb-3 md:mb-4 text-gray-900 truncate">
              {portfolio.name}
            </h2>

            {/* Total Value */}
            <div className="mb-2 md:mb-3">
              <p className="text-xs md:text-sm text-gray-600">Total Value</p>
              <p className="text-xl md:text-2xl font-bold text-gray-900">
                {formatCurrency(portfolio.total_value_usd)}
              </p>
            </div>

            {/* Total Return */}
            <div className="mb-2 md:mb-3">
              <p className="text-xs md:text-sm text-gray-600">Total Return</p>
              <p className={`text-base md:text-lg font-semibold ${getChangeColor(portfolio.total_return_pct)}`}>
                {formatPercent(portfolio.total_return_pct)}
              </p>
            </div>

            {/* Position Count */}
            <div className="pt-2 md:pt-3 border-t border-gray-200">
              <p className="text-xs md:text-sm text-gray-600">
                {portfolio.position_count} {portfolio.position_count === 1 ? 'position' : 'positions'}
              </p>
            </div>
          </div>
        ))}
      </div>

      {/* Create Portfolio Modal */}
      <CreatePortfolioModal
        isOpen={isCreateModalOpen}
        onClose={handleModalClose}
        onSuccess={handleModalSuccess}
      />
    </div>
  )
}

export default PortfolioList
