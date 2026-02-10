import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { transactionApi, assetApi, portfolioApi } from '../services/api'
import { useToast } from '../components/ToastContainer'

function AddTransaction() {
  const navigate = useNavigate()
  const toast = useToast()
  const [searchParams] = useSearchParams()
  const preselectedAssetId = searchParams.get('asset_id')
  const portfolioIdParam = searchParams.get('portfolio_id')

  const [formData, setFormData] = useState({
    portfolio_id: portfolioIdParam ? parseInt(portfolioIdParam) : 1,
    asset_id: preselectedAssetId || '',
    transaction_type: 'buy',
    quantity: '',
    price: '',
    fee: '0',
    timestamp: new Date().toISOString().slice(0, 16), // YYYY-MM-DDTHH:MM format
    notes: ''
  })

  const [assets, setAssets] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [portfolio, setPortfolio] = useState(null)
  const [portfolioLoading, setPortfolioLoading] = useState(true)
  const [portfolioError, setPortfolioError] = useState(null)

  // Fetch portfolio details
  useEffect(() => {
    const fetchPortfolio = async () => {
      try {
        setPortfolioLoading(true)
        setPortfolioError(null)
        const response = await portfolioApi.getPortfolio(formData.portfolio_id)
        setPortfolio(response.data)
      } catch (err) {
        console.error('Error fetching portfolio:', err)
        const errorMessage = err.response?.data?.error?.message 
          || err.response?.data?.detail 
          || err.message 
          || 'Failed to load portfolio information'
        setPortfolioError(errorMessage)
      } finally {
        setPortfolioLoading(false)
      }
    }

    if (formData.portfolio_id) {
      fetchPortfolio()
    }
  }, [formData.portfolio_id])

  // Search assets for dropdown
  useEffect(() => {
    const searchAssets = async () => {
      if (!searchQuery.trim()) {
        setAssets([])
        return
      }

      try {
        const response = await assetApi.search(searchQuery, 10)
        setAssets(response.data.assets || [])
      } catch (err) {
        console.error('Error searching assets:', err)
      }
    }

    const timeoutId = setTimeout(searchAssets, 300)
    return () => clearTimeout(timeoutId)
  }, [searchQuery])

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!formData.asset_id || !formData.quantity || !formData.price) {
      setError('Please fill in all required fields')
      return
    }

    try {
      setLoading(true)
      setError(null)
      
      const transactionData = {
        ...formData,
        quantity: parseFloat(formData.quantity),
        price: parseFloat(formData.price),
        fee: parseFloat(formData.fee) || 0,
      }

      await transactionApi.create(transactionData)
      toast.success('Transaction added successfully!')
      navigate(`/portfolios/${formData.portfolio_id}`)
    } catch (err) {
      const errorMessage = err.response?.data?.error?.message 
        || err.response?.data?.detail 
        || err.message 
        || 'Failed to add transaction'
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const retryFetchPortfolio = () => {
    setPortfolioError(null)
    setPortfolioLoading(true)
    // Trigger re-fetch by updating a dependency
    setFormData(prev => ({ ...prev }))
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-white rounded-lg shadow p-6">
        <h1 className="text-2xl font-bold mb-2">Add Transaction</h1>
        
        {/* Portfolio Information */}
        {portfolioLoading ? (
          <div className="mb-6 p-3 bg-gray-50 border border-gray-200 rounded-md flex items-center">
            <svg 
              className="animate-spin h-5 w-5 text-gray-600 mr-2" 
              xmlns="http://www.w3.org/2000/svg" 
              fill="none" 
              viewBox="0 0 24 24"
            >
              <circle 
                className="opacity-25" 
                cx="12" 
                cy="12" 
                r="10" 
                stroke="currentColor" 
                strokeWidth="4"
              />
              <path 
                className="opacity-75" 
                fill="currentColor" 
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            <p className="text-sm text-gray-600">Loading portfolio...</p>
          </div>
        ) : portfolioError ? (
          <div className="mb-6 p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-800 mb-2">{portfolioError}</p>
            <button
              onClick={retryFetchPortfolio}
              className="text-sm text-red-600 hover:text-red-800 font-medium underline"
            >
              Retry loading portfolio
            </button>
          </div>
        ) : portfolio ? (
          <div className="mb-6 p-3 bg-blue-50 border border-blue-200 rounded-md">
            <p className="text-sm text-gray-600">Adding transaction to:</p>
            <p className="text-lg font-semibold text-gray-800">{portfolio.name}</p>
          </div>
        ) : (
          <div className="mb-6 p-3 bg-gray-50 border border-gray-200 rounded-md">
            <p className="text-sm text-gray-600">Portfolio ID: {formData.portfolio_id}</p>
          </div>
        )}

        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Asset Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Asset *
            </label>
            {preselectedAssetId ? (
              <p className="text-gray-600">Asset ID: {preselectedAssetId}</p>
            ) : (
              <div className="space-y-2">
                <input
                  type="text"
                  placeholder="Search for asset..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary focus:border-transparent"
                />
                {assets.length > 0 && (
                  <div className="border border-gray-300 rounded-md max-h-40 overflow-y-auto">
                    {assets.map((asset) => (
                      <button
                        key={asset.id}
                        type="button"
                        onClick={() => {
                          setFormData(prev => ({ ...prev, asset_id: asset.id }))
                          setSearchQuery(`${asset.symbol} - ${asset.name}`)
                          setAssets([])
                        }}
                        className="w-full text-left px-3 py-2 hover:bg-gray-50 border-b border-gray-200 last:border-b-0"
                      >
                        <div>
                          <span className="font-medium">{asset.symbol}</span>
                          <span className="text-gray-600 ml-2">{asset.name}</span>
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Transaction Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Transaction Type *
            </label>
            <select
              name="transaction_type"
              value={formData.transaction_type}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary focus:border-transparent"
            >
              <option value="buy">Buy</option>
              <option value="sell">Sell</option>
            </select>
          </div>

          {/* Quantity */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Quantity *
            </label>
            <input
              type="number"
              name="quantity"
              value={formData.quantity}
              onChange={handleInputChange}
              step="0.000001"
              min="0"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary focus:border-transparent"
            />
          </div>

          {/* Price */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Price per Unit *
            </label>
            <input
              type="number"
              name="price"
              value={formData.price}
              onChange={handleInputChange}
              step="0.01"
              min="0"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary focus:border-transparent"
            />
          </div>

          {/* Fee */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Fee (Optional)
            </label>
            <input
              type="number"
              name="fee"
              value={formData.fee}
              onChange={handleInputChange}
              step="0.01"
              min="0"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary focus:border-transparent"
            />
          </div>

          {/* Date & Time */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Date & Time *
            </label>
            <input
              type="datetime-local"
              name="timestamp"
              value={formData.timestamp}
              onChange={handleInputChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary focus:border-transparent"
            />
          </div>

          {/* Notes */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Notes (Optional)
            </label>
            <textarea
              name="notes"
              value={formData.notes}
              onChange={handleInputChange}
              rows="3"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary focus:border-transparent"
            />
          </div>

          {/* Submit Buttons */}
          <div className="flex space-x-4">
            <button
              type="submit"
              disabled={loading}
              className="flex-1 bg-primary text-white py-2 px-4 rounded-md hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Adding Transaction...' : 'Add Transaction'}
            </button>
            <button
              type="button"
              onClick={() => navigate(`/portfolios/${formData.portfolio_id}`)}
              className="flex-1 bg-gray-300 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-400"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default AddTransaction