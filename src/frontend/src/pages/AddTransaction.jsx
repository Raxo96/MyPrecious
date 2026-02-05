import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { transactionApi, assetApi } from '../services/api'

function AddTransaction() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const preselectedAssetId = searchParams.get('asset_id')

  const [formData, setFormData] = useState({
    portfolio_id: 1, // Hardcoded for MVP
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
      navigate('/', { 
        state: { message: 'Transaction added successfully!' }
      })
    } catch (err) {
      setError(err.response?.data?.error?.message || err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-white rounded-lg shadow p-6">
        <h1 className="text-2xl font-bold mb-6">Add Transaction</h1>

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
              onClick={() => navigate('/')}
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