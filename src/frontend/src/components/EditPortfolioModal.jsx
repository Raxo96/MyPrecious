import { useState, useEffect } from 'react'
import { portfolioApi } from '../services/api'

function EditPortfolioModal({ isOpen, onClose, onSuccess, portfolio }) {
  const [formData, setFormData] = useState({
    name: ''
  })
  const [errors, setErrors] = useState({})
  const [loading, setLoading] = useState(false)
  const [apiError, setApiError] = useState(null)

  // Pre-fill form with current portfolio name when modal opens or portfolio changes
  useEffect(() => {
    if (isOpen && portfolio) {
      setFormData({
        name: portfolio.name || ''
      })
      // Clear any previous errors
      setErrors({})
      setApiError(null)
    }
  }, [isOpen, portfolio])

  // Handle ESC key to close modal
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape' && isOpen && !loading) {
        handleClose()
      }
    }

    if (isOpen) {
      document.addEventListener('keydown', handleEscape)
      // Prevent body scroll when modal is open
      document.body.style.overflow = 'hidden'
    }

    return () => {
      document.removeEventListener('keydown', handleEscape)
      document.body.style.overflow = 'unset'
    }
  }, [isOpen, loading])

  // Don't render if not open
  if (!isOpen) return null

  const validateForm = () => {
    const newErrors = {}
    
    // Validate name is not empty or whitespace
    if (!formData.name.trim()) {
      newErrors.name = 'Portfolio name is required'
    }
    
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
    
    // Clear error for this field when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: null
      }))
    }
    
    // Clear API error when user makes changes
    if (apiError) {
      setApiError(null)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    // Validate form
    if (!validateForm()) {
      return
    }

    // Check if portfolio exists
    if (!portfolio || !portfolio.id) {
      setApiError('Invalid portfolio')
      return
    }

    try {
      setLoading(true)
      setApiError(null)
      
      // Call API to update portfolio
      await portfolioApi.update(portfolio.id, {
        name: formData.name.trim()
      })
      
      // Reset form
      setFormData({ name: '' })
      setErrors({})
      
      // Call success callback to refresh data
      if (onSuccess) {
        onSuccess()
      }
      
      // Close modal
      onClose()
    } catch (err) {
      const errorMessage = err.response?.data?.error?.message 
        || err.response?.data?.detail 
        || err.message 
        || 'Failed to update portfolio'
      setApiError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const handleClose = () => {
    // Reset form and errors when closing
    setFormData({ name: '' })
    setErrors({})
    setApiError(null)
    onClose()
  }

  const handleBackdropClick = (e) => {
    // Close modal if clicking on backdrop (not the modal content)
    if (e.target === e.currentTarget) {
      handleClose()
    }
  }

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 animate-fade-in p-4"
      onClick={handleBackdropClick}
    >
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 animate-slide-in-up">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Edit Portfolio</h2>
        </div>

        {/* Modal Body */}
        <form onSubmit={handleSubmit}>
          <div className="px-6 py-4 space-y-4">
            {/* API Error Message */}
            {apiError && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-md">
                <p className="text-sm text-red-800">{apiError}</p>
              </div>
            )}

            {/* Portfolio Name Input */}
            <div>
              <label 
                htmlFor="name" 
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Portfolio Name *
              </label>
              <input
                type="text"
                id="name"
                name="name"
                value={formData.name}
                onChange={handleInputChange}
                placeholder="e.g., Tech Stocks, Retirement Fund"
                className={`w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                  errors.name ? 'border-red-500' : 'border-gray-300'
                }`}
                autoFocus
              />
              {errors.name && (
                <p className="mt-1 text-sm text-red-600">{errors.name}</p>
              )}
            </div>
          </div>

          {/* Modal Footer */}
          <div className="px-6 py-4 border-t border-gray-200 flex justify-end space-x-3">
            <button
              type="button"
              onClick={handleClose}
              disabled={loading}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default EditPortfolioModal
