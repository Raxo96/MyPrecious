import { useState, useEffect } from 'react'
import { portfolioApi } from '../services/api'

function DeletePortfolioConfirmation({ isOpen, onClose, onSuccess, portfolio }) {
  const [loading, setLoading] = useState(false)
  const [apiError, setApiError] = useState(null)

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

  const handleDelete = async () => {
    // Check if portfolio exists
    if (!portfolio || !portfolio.id) {
      setApiError('Invalid portfolio')
      return
    }

    try {
      setLoading(true)
      setApiError(null)
      
      // Call API to delete portfolio
      await portfolioApi.delete(portfolio.id)
      
      // Call success callback to handle navigation
      if (onSuccess) {
        onSuccess()
      }
      
      // Close modal
      onClose()
    } catch (err) {
      const errorMessage = err.response?.data?.error?.message 
        || err.response?.data?.detail 
        || err.message 
        || 'Failed to delete portfolio'
      setApiError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const handleClose = () => {
    // Reset error when closing
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
        {/* Modal Header - Red/Danger Theme */}
        <div className="px-6 py-4 border-b border-red-200 bg-red-50">
          <h2 className="text-xl font-semibold text-red-900">Delete Portfolio</h2>
        </div>

        {/* Modal Body */}
        <div className="px-6 py-4 space-y-4">
          {/* API Error Message */}
          {apiError && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-md">
              <p className="text-sm text-red-800">{apiError}</p>
            </div>
          )}

          {/* Warning Icon */}
          <div className="flex items-center justify-center">
            <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center">
              <svg 
                className="w-6 h-6 text-red-600" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth={2} 
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" 
                />
              </svg>
            </div>
          </div>

          {/* Warning Message */}
          <div className="text-center">
            <p className="text-gray-900 font-medium mb-2">
              Are you sure you want to delete this portfolio?
            </p>
            {portfolio && (
              <p className="text-lg font-semibold text-gray-900 mb-3">
                "{portfolio.name}"
              </p>
            )}
            <p className="text-sm text-gray-600">
              This action cannot be undone. All portfolio data, including stock holdings and transaction history, will be permanently deleted.
            </p>
          </div>
        </div>

        {/* Modal Footer - Red/Danger Theme */}
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
            type="button"
            onClick={handleDelete}
            disabled={loading}
            className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Deleting...' : 'Delete Portfolio'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default DeletePortfolioConfirmation
